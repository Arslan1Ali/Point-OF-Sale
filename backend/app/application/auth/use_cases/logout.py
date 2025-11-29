from __future__ import annotations

from dataclasses import dataclass

import jwt

from app.application.auth.ports import RefreshTokenRepositoryPort, TokenProviderPort
from app.domain.common.errors import RefreshTokenNotFoundError, TokenError


@dataclass
class LogoutInput:
    refresh_token: str


class LogoutUseCase:
    def __init__(self, tokens: TokenProviderPort, refresh_tokens: RefreshTokenRepositoryPort):
        self._tokens = tokens
        self._refresh_tokens = refresh_tokens

    async def execute(self, data: LogoutInput) -> None:
        try:
            payload = self._tokens.decode_token(data.refresh_token)
        except jwt.PyJWTError as exc:
            raise TokenError("invalid token") from exc

        if payload.get("type") != "refresh":
            raise TokenError("invalid token type")

        token_id = payload.get("jti")
        if not token_id:
            raise TokenError("invalid token")

        user_id = payload.get("sub")
        if not user_id:
            raise TokenError("invalid token")

        stored = await self._refresh_tokens.get_by_id(token_id)
        if stored is None:
            raise RefreshTokenNotFoundError()
        if stored.user_id != user_id:
            raise TokenError("invalid token")

        await self._refresh_tokens.revoke(token_id)
