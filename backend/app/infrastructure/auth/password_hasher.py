from __future__ import annotations

from passlib.context import CryptContext

from app.domain.common.errors import ValidationError

_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class PasswordHasher:
    def hash(self, raw: str) -> str:
        if not raw or len(raw) < 8:
            raise ValidationError("Password too short", code="user.password_too_short")
        return _pwd_context.hash(raw)

    def verify(self, raw: str, hashed: str) -> bool:  # pragma: no cover - simple wrapper
        return _pwd_context.verify(raw, hashed)


# Backwards compatible functional helpers if any earlier code used them
def hash_password(raw: str) -> str:  # pragma: no cover
    return PasswordHasher().hash(raw)


def verify_password(raw: str, hashed: str) -> bool:  # pragma: no cover
    return PasswordHasher().verify(raw, hashed)
