from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.application.auth.use_cases.list_users import ListUsersInput, ListUsersResult, ListUsersUseCase
from app.domain.auth.entities import User, UserRole
from app.shared.pagination import PageParams


@dataclass
class FakeUserRepo:
    users: list[User]
    total: int

    async def search(self, **kwargs):  # type: ignore[no-untyped-def]
        return self.users, self.total


@pytest.mark.asyncio
async def test_list_users_returns_page():
    user = User.create(email="admin@example.com", password_hash="hashed-password", role=UserRole.ADMIN)
    repo = FakeUserRepo(users=[user], total=1)
    use_case = ListUsersUseCase(repo)  # type: ignore[arg-type]

    params = PageParams(page=1, limit=10)
    result = await use_case.execute(ListUsersInput(params=params))

    assert isinstance(result, ListUsersResult)
    assert result.meta.total == 1
    assert result.items == [user]