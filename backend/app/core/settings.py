from __future__ import annotations

import json
from functools import lru_cache
from typing import ClassVar, Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    _DEFAULT_SECRET_SENTINEL: ClassVar[str] = "CHANGE_ME"

    ENV: Literal["dev", "test", "staging", "prod"] = "dev"
    DEBUG: bool = False

    APP_NAME: str = "retail-pos-backend"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"  # Development default; override outside dev/test.
    DATABASE_ECHO: bool | None = None

    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    JWT_ALGORITHM: str = "HS256"
    JWT_SECRET_KEY: str = _DEFAULT_SECRET_SENTINEL
    JWT_ISSUER: str = "retail-pos"

    # CORS / Hosts
    CORS_ORIGINS: list[str] = []
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: list[str] = [
        "Authorization",
        "Content-Type",
        "X-Requested-With",
        "X-Trace-Id",
    ]
    ALLOWED_HOSTS: list[str] = ["*"]

    # Observability (placeholders)
    ENABLE_TRACING: bool = False

    # Cache
    REDIS_URL: str = "redis://localhost:6379/0"

    @property
    def database_echo(self) -> bool:
        return self.DATABASE_ECHO if self.DATABASE_ECHO is not None else self.DEBUG

    @field_validator("CORS_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def _split_csv(cls, value: list[str] | str | None) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("[") and stripped.endswith("]"):
                try:
                    parsed = json.loads(stripped)
                except json.JSONDecodeError:
                    pass
                else:
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return list(value)

    @model_validator(mode="after")
    def _enforce_secure_defaults(self) -> "Settings":
        if self.ENV in {"staging", "prod"}:
            if not self.CORS_ORIGINS:
                raise ValueError("CORS_ORIGINS must be configured for staging/prod environments")
            if any(host == "*" for host in self.ALLOWED_HOSTS):
                raise ValueError("ALLOWED_HOSTS cannot contain '*' outside dev/test")
            if self.JWT_SECRET_KEY == self._DEFAULT_SECRET_SENTINEL:
                raise ValueError("JWT_SECRET_KEY must be overridden for staging/prod environments")
            if self.DATABASE_URL.startswith("sqlite+"):
                raise ValueError("DATABASE_URL must point to Postgres in staging/prod environments")
        return self


@lru_cache
def get_settings() -> Settings:  # pragma: no cover - trivial
    return Settings()
