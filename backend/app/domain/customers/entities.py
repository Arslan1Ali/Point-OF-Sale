from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.common.errors import ValidationError
from app.domain.common.identifiers import new_ulid

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(slots=True)
class Customer:
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: int = 0

    @staticmethod
    def normalize_email(email: str) -> str:
        if not email or not email.strip():
            raise ValidationError("email is required", code="customer.invalid_email")
        normalized_email = email.strip().lower()
        if not _EMAIL_PATTERN.match(normalized_email):
            raise ValidationError("email format is invalid", code="customer.invalid_email")
        return normalized_email

    @staticmethod
    def register(
        *,
        first_name: str,
        last_name: str,
        email: str,
        phone: str | None = None,
    ) -> Customer:
        if not first_name or not first_name.strip():
            raise ValidationError("first_name is required", code="customer.invalid_first_name")
        if not last_name or not last_name.strip():
            raise ValidationError("last_name is required", code="customer.invalid_last_name")
        normalized_email = Customer.normalize_email(email)
        normalized_first = first_name.strip().title()
        normalized_last = last_name.strip().title()
        normalized_phone = phone.strip() if phone and phone.strip() else None
        return Customer(
            id=new_ulid(),
            first_name=normalized_first,
            last_name=normalized_last,
            email=normalized_email,
            phone=normalized_phone,
        )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def update_contact(self, *, email: str | None = None, phone: str | None = None) -> bool:
        changed = False
        if email is not None:
            normalized_email = self.normalize_email(email)
            if normalized_email != self.email:
                self.email = normalized_email
                changed = True
        if phone is not None:
            normalized_phone = phone.strip() if phone and phone.strip() else None
            if normalized_phone != self.phone:
                self.phone = normalized_phone
                changed = True
        if changed:
            self._touch()
        return changed

    def rename(self, *, first_name: str | None = None, last_name: str | None = None) -> bool:
        changed = False
        if first_name is not None:
            normalized_first = first_name.strip()
            if not normalized_first:
                raise ValidationError("first_name is required", code="customer.invalid_first_name")
            normalized_first = normalized_first.title()
            if normalized_first != self.first_name:
                self.first_name = normalized_first
                changed = True
        if last_name is not None:
            normalized_last = last_name.strip()
            if not normalized_last:
                raise ValidationError("last_name is required", code="customer.invalid_last_name")
            normalized_last = normalized_last.title()
            if normalized_last != self.last_name:
                self.last_name = normalized_last
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

    def _touch(self) -> None:
        self.version += 1
        self.updated_at = datetime.now(UTC)
