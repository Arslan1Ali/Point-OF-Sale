from __future__ import annotations

from dataclasses import dataclass

from app.application.auth.ports import (
    PasswordHasherPort,
    RefreshTokenRepositoryPort,
    TokenProviderPort,
    UserRepositoryPort,
)
from app.domain.auth.entities import RefreshToken
from app.domain.common.errors import UnauthorizedError


@dataclass
class LoginInput:
    email: str
    password: str


@dataclass
class LoginOutput:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginUseCase:
    def __init__(
        self,
        repo: UserRepositoryPort,
        hasher: PasswordHasherPort,
        tokens: TokenProviderPort,
        refresh_tokens: RefreshTokenRepositoryPort,
    ):
        self._repo = repo
        self._hasher = hasher
        self._tokens = tokens
        self._refresh_repo = refresh_tokens

    async def execute(self, data: LoginInput) -> LoginOutput:
        user = await self._repo.get_by_email(data.email)
        if not user:
            raise UnauthorizedError("invalid credentials")
        if not self._hasher.verify(data.password, user.password_hash):
            raise UnauthorizedError("invalid credentials")
        access = self._tokens.create_access_token(subject=user.id, extra={"role": user.role})
        refresh_token, refresh_id, refresh_expires = self._tokens.create_refresh_token_with_id(subject=user.id)
        entity = RefreshToken.issue(user_id=user.id, expires_at=refresh_expires, token_id=refresh_id)
        await self._refresh_repo.add(entity)
        return LoginOutput(access_token=access, refresh_token=refresh_token)