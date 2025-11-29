from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.common.errors import ValidationError
from app.domain.common.identifiers import new_ulid

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(slots=True)
class Supplier:
    id: str
    name: str
    contact_email: str | None = None
    contact_phone: str | None = None
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: int = 0

    @staticmethod
    def normalize_name(name: str) -> str:
        if not name or not name.strip():
            raise ValidationError("Supplier name is required", code="supplier.invalid_name")
        normalized = " ".join(part for part in name.strip().split() if part)
        if not normalized:
            raise ValidationError("Supplier name is required", code="supplier.invalid_name")
        return normalized

    @staticmethod
    def normalize_email(email: str) -> str:
        normalized = email.strip().lower()
        if not _EMAIL_PATTERN.match(normalized):
            raise ValidationError("Email format is invalid", code="supplier.invalid_email")
        return normalized

    @staticmethod
    def register(*, name: str, contact_email: str | None = None, contact_phone: str | None = None) -> Supplier:
        normalized_name = Supplier.normalize_name(name)
        normalized_email = Supplier.normalize_email(contact_email) if contact_email else None
        normalized_phone = contact_phone.strip() if contact_phone and contact_phone.strip() else None
        return Supplier(
            id=new_ulid(),
            name=normalized_name,
            contact_email=normalized_email,
            contact_phone=normalized_phone,
        )

    def rename(self, name: str) -> bool:
        normalized = self.normalize_name(name)
        if normalized == self.name:
            return False
        self.name = normalized
        self._touch()
        return True

    def update_contact(
        self,
        *,
        contact_email: str | None = None,
        contact_phone: str | None = None,
    ) -> bool:
        changed = False
        if contact_email is not None:
            normalized_email = self.normalize_email(contact_email)
            if normalized_email != self.contact_email:
                self.contact_email = normalized_email
                changed = True
        if contact_phone is not None:
            normalized_phone = contact_phone.strip() if contact_phone and contact_phone.strip() else None
            if normalized_phone != self.contact_phone:
                self.contact_phone = normalized_phone
                changed = True
        if changed:
            self._touch()
        return changed

    def deactivate(self) -> bool:
        if not self.active:
            return False
        self.active = False
        self._touch()
        return True

    def reactivate(self) -> bool:
        if self.active:
            return False
        self.active = True
        self._touch()
        return True

    def _touch(self) -> None:
        self.version += 1
        self.updated_at = datetime.now(UTC)
