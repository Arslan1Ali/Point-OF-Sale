from __future__ import annotations

from dataclasses import dataclass

from app.application.auth.ports import UserRepositoryPort
from app.domain.auth.entities import User, UserRole
from app.domain.common.errors import ConflictError, NotFoundError, ValidationError


@dataclass(slots=True)
class ChangeUserRoleInput:
    user_id: str
    expected_version: int
    role: UserRole


class ChangeUserRoleUseCase:
    def __init__(self, users: UserRepositoryPort):
        self._users = users

    async def execute(self, data: ChangeUserRoleInput) -> User:
        user = await self._users.get_by_id(data.user_id)
        if user is None:
            raise NotFoundError("user not found")
        if user.version != data.expected_version:
            raise ConflictError("user modified by another transaction")
        if user.role == data.role:
            raise ValidationError("user already has role", code="user_role_unchanged")
        user.change_role(data.role)
        updated = await self._users.update(user, expected_version=data.expected_version)
        if not updated:
            raise ConflictError("user modified by another transaction")
        return user
