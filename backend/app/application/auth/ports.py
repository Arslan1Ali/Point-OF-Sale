from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from app.domain.auth.admin_action_log import AdminActionLog
from app.domain.auth.entities import RefreshToken, User, UserRole
from app.shared.pagination import PageParams


class UserRepositoryPort(Protocol):
    async def add(self, user: User) -> None: ...  # noqa: E701
    async def get_by_email(self, email: str) -> User | None: ...  # noqa: E701
    async def get_by_id(self, user_id: str) -> User | None: ...  # noqa: E701
    async def update(self, user: User, expected_version: int) -> bool: ...  # noqa: E701
    async def search(
        self,
        *,
        email: str | None,
        role: UserRole | None,
        active: bool | None,
        params: PageParams,
    ) -> tuple[list[User], int]: ...  # noqa: E701


class RefreshTokenRepositoryPort(Protocol):
    async def add(self, token: RefreshToken) -> None: ...  # noqa: E701
    async def get_by_id(self, token_id: str) -> RefreshToken | None: ...  # noqa: E701
    async def revoke_and_replace(
        self,
        token_id: str,
        replacement: RefreshToken | None,
    ) -> RefreshToken | None: ...  # noqa: E701
    async def revoke(self, token_id: str) -> RefreshToken | None: ...  # noqa: E701
    async def revoke_all_for_user(self, user_id: str) -> int: ...  # noqa: E701


class PasswordHasherPort(Protocol):
    def hash(self, raw: str) -> str: ...  # noqa: E701
    def verify(self, raw: str, hashed: str) -> bool: ...  # noqa: E701


class TokenProviderPort(Protocol):
    def create_access_token(self, subject: str, extra: dict[str, Any] | None = None) -> str: ...  # noqa: E701
    def create_refresh_token(self, subject: str) -> str: ...  # noqa: E701
    def create_refresh_token_with_id(self, subject: str, token_id: str | None = None) -> tuple[str, str, datetime]: ...  # noqa: E701
    def decode_token(self, token: str) -> dict[str, Any]: ...  # noqa: E701


class AdminActionLogRepositoryPort(Protocol):
    async def add(self, log: AdminActionLog) -> None: ...  # noqa: E701
    async def search(
        self,
        *,
        actor_user_id: str | None,
        target_user_id: str | None,
        action: str | None,
        start: datetime | None,
        end: datetime | None,
        params: PageParams,
    ) -> tuple[list[AdminActionLog], int]: ...  # noqa: E701
