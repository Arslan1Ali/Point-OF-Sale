from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.auth.entities import RefreshToken
from app.infrastructure.db.models.auth.refresh_token_model import RefreshTokenModel


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, token: RefreshToken) -> None:
        self._session.add(self._to_model(token))
        await self._session.flush()

    async def get_by_id(self, token_id: str) -> RefreshToken | None:
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.id == token_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    async def revoke_and_replace(
        self,
        token_id: str,
        replacement: RefreshToken | None,
    ) -> RefreshToken | None:
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.id == token_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        if not model.revoked:
            model.revoked = True
            model.replaced_by = replacement.id if replacement else None
            model.version += 1
        if replacement is not None:
            self._session.add(self._to_model(replacement))
        await self._session.flush()
        return self._to_entity(model)

    async def revoke(self, token_id: str) -> RefreshToken | None:
        return await self.revoke_and_replace(token_id, None)

    async def revoke_all_for_user(self, user_id: str) -> int:
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.user_id == user_id,
            RefreshTokenModel.revoked.is_(False),
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        for model in models:
            model.revoked = True
            model.replaced_by = None
            model.version += 1
        if models:
            await self._session.flush()
        return len(models)

    @staticmethod
    def _to_entity(model: RefreshTokenModel) -> RefreshToken:
        return RefreshToken(
            id=model.id,
            user_id=model.user_id,
            revoked=model.revoked,
            replaced_by=model.replaced_by,
            created_at=RefreshTokenRepository._ensure_aware(model.created_at),
            expires_at=RefreshTokenRepository._ensure_aware(model.expires_at),
            version=model.version,
        )

    @staticmethod
    def _to_model(token: RefreshToken) -> RefreshTokenModel:
        return RefreshTokenModel(
            id=token.id,
            user_id=token.user_id,
            revoked=token.revoked,
            replaced_by=token.replaced_by,
            created_at=token.created_at,
            expires_at=token.expires_at,
            version=token.version,
        )

    @staticmethod
    def _ensure_aware(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
