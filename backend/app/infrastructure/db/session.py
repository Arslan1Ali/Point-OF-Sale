from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.settings import get_settings


class Base(DeclarativeBase):
    pass


_settings = get_settings()
engine = create_async_engine(_settings.DATABASE_URL, echo=_settings.database_echo)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
# Export factory alias for tests
async_session_factory = AsyncSessionLocal


async def get_session() -> AsyncGenerator[AsyncSession, None]:  # FastAPI dependency
    async with AsyncSessionLocal() as session:  # pragma: no cover - thin wrapper
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
