from __future__ import annotations

import copy
from datetime import UTC, datetime

import pytest

from app.application.auth.use_cases.activate_user import ActivateUserInput, ActivateUserUseCase
from app.application.auth.use_cases.change_user_role import ChangeUserRoleInput, ChangeUserRoleUseCase
from app.application.auth.use_cases.deactivate_user import DeactivateUserInput, DeactivateUserUseCase
from app.application.auth.use_cases.reset_user_password import (
    ResetUserPasswordInput,
    ResetUserPasswordUseCase,
)
from app.domain.auth.entities import User, UserRole
from app.domain.common.errors import ConflictError, ValidationError
from app.domain.common.identifiers import new_ulid


def _make_user(
    *,
    active: bool = True,
    role: UserRole = UserRole.CASHIER,
    version: int = 0,
    password_hash: str = "hashed::startpass",
) -> User:
    now = datetime.now(UTC)
    return User(
        id=new_ulid(),
        email="user@example.com",
        password_hash=password_hash,
        role=role,
        active=active,
        created_at=now,
        updated_at=now,
        version=version,
    )


class FakeUserRepository:
    def __init__(self, user: User | None) -> None:
        self._stored_user = copy.deepcopy(user) if user else None

    async def add(self, user: User) -> None:  # pragma: no cover - unused in tests
        raise NotImplementedError

    async def get_by_email(self, email: str) -> User | None:  # pragma: no cover - unused in tests
        raise NotImplementedError

    async def get_by_id(self, user_id: str) -> User | None:
        if self._stored_user and self._stored_user.id == user_id:
            return copy.deepcopy(self._stored_user)
        return None

    async def update(self, user: User, expected_version: int) -> bool:
        if self._stored_user is None or self._stored_user.id != user.id:
            return False
        if self._stored_user.version != expected_version:
            return False
        self._stored_user = copy.deepcopy(user)
        return True


class FakeHasher:
    def hash(self, raw: str) -> str:
        if not raw or len(raw) < 6:
            raise ValidationError("password too short")
        return f"hashed::{raw}"

    def verify(self, raw: str, hashed: str) -> bool:
        return hashed == f"hashed::{raw}"


@pytest.mark.asyncio
async def test_activate_user_reactivates_and_increments_version():
    original = _make_user(active=False, version=2)
    repo = FakeUserRepository(original)
    use_case = ActivateUserUseCase(repo)

    result = await use_case.execute(ActivateUserInput(user_id=original.id, expected_version=original.version))

    assert result.active is True
    assert result.version == original.version + 1
    stored = await repo.get_by_id(original.id)
    assert stored is not None and stored.active is True and stored.version == result.version


@pytest.mark.asyncio
async def test_activate_user_raises_when_already_active():
    user = _make_user(active=True, version=1)
    repo = FakeUserRepository(user)
    use_case = ActivateUserUseCase(repo)

    with pytest.raises(ValidationError) as exc:
        await use_case.execute(ActivateUserInput(user_id=user.id, expected_version=user.version))
    assert exc.value.error_code == "user_already_active"


@pytest.mark.asyncio
async def test_deactivate_user_sets_flag_and_version():
    user = _make_user(active=True, version=3)
    repo = FakeUserRepository(user)
    use_case = DeactivateUserUseCase(repo)

    result = await use_case.execute(DeactivateUserInput(user_id=user.id, expected_version=user.version))

    assert result.active is False
    assert result.version == user.version + 1
    stored = await repo.get_by_id(user.id)
    assert stored is not None and stored.active is False


@pytest.mark.asyncio
async def test_change_user_role_requires_new_role():
    user = _make_user(role=UserRole.MANAGER, version=4)
    repo = FakeUserRepository(user)
    use_case = ChangeUserRoleUseCase(repo)

    with pytest.raises(ValidationError) as exc:
        await use_case.execute(
            ChangeUserRoleInput(user_id=user.id, expected_version=user.version, role=user.role)
        )
    assert exc.value.error_code == "user_role_unchanged"


@pytest.mark.asyncio
async def test_change_user_role_detects_version_conflict():
    user = _make_user(role=UserRole.CASHIER, version=2)
    repo = FakeUserRepository(user)
    use_case = ChangeUserRoleUseCase(repo)

    with pytest.raises(ConflictError):
        await use_case.execute(
            ChangeUserRoleInput(user_id=user.id, expected_version=user.version - 1, role=UserRole.MANAGER)
        )


@pytest.mark.asyncio
async def test_reset_password_updates_hash_and_version():
    hasher = FakeHasher()
    user = _make_user(password_hash=hasher.hash("CurrentPass1!"), version=5)
    repo = FakeUserRepository(user)
    use_case = ResetUserPasswordUseCase(repo, hasher)

    result = await use_case.execute(
        ResetUserPasswordInput(
            user_id=user.id,
            expected_version=user.version,
            new_password="N3wSecretPass!",
        )
    )

    assert hasher.verify("N3wSecretPass!", result.password_hash)
    assert result.version == user.version + 1
    stored = await repo.get_by_id(user.id)
    assert stored is not None and hasher.verify("N3wSecretPass!", stored.password_hash)


@pytest.mark.asyncio
async def test_reset_password_rejects_same_password():
    hasher = FakeHasher()
    user = _make_user(password_hash=hasher.hash("SamePass1!"), version=1)
    repo = FakeUserRepository(user)
    use_case = ResetUserPasswordUseCase(repo, hasher)

    with pytest.raises(ValidationError) as exc:
        await use_case.execute(
            ResetUserPasswordInput(
                user_id=user.id,
                expected_version=user.version,
                new_password="SamePass1!",
            )
        )
    assert exc.value.error_code == "password_unchanged"
