from __future__ import annotations

from dataclasses import dataclass

from app.application.auth.ports import UserRepositoryPort
from app.domain.auth.entities import User
from app.domain.common.errors import ConflictError, NotFoundError, ValidationError


@dataclass(slots=True)
class ActivateUserInput:
    user_id: str
    expected_version: int


class ActivateUserUseCase:
    def __init__(self, users: UserRepositoryPort):
        self._users = users

    async def execute(self, data: ActivateUserInput) -> User:
        user = await self._users.get_by_id(data.user_id)
        if user is None:
            raise NotFoundError("user not found")
        if user.version != data.expected_version:
            raise ConflictError("user modified by another transaction")
        if user.active:
            raise ValidationError("user already active", code="user_already_active")
        user.activate()
        updated = await self._users.update(user, expected_version=data.expected_version)
        if not updated:
            raise ConflictError("user modified by another transaction")
        return user
