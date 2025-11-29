from __future__ import annotations

from dataclasses import dataclass

from app.application.auth.ports import UserRepositoryPort
from app.domain.auth.entities import User
from app.domain.common.errors import InactiveUserError, UnauthorizedError


@dataclass
class GetCurrentUserInput:
    user_id: str


class GetCurrentUserUseCase:
    def __init__(self, users: UserRepositoryPort):
        self._users = users

    async def execute(self, data: GetCurrentUserInput) -> User:
        user = await self._users.get_by_id(data.user_id)
        if user is None:
            raise UnauthorizedError("user not found", code="user_not_found")
        if not user.active:
            raise InactiveUserError()
        return user
