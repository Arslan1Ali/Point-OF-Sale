from __future__ import annotations

from dataclasses import dataclass

from app.application.auth.ports import RefreshTokenRepositoryPort


@dataclass
class LogoutAllSessionsInput:
    user_id: str


class LogoutAllSessionsUseCase:
    def __init__(self, refresh_tokens: RefreshTokenRepositoryPort):
        self._refresh_tokens = refresh_tokens

    async def execute(self, data: LogoutAllSessionsInput) -> int:
        return await self._refresh_tokens.revoke_all_for_user(data.user_id)
