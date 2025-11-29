from __future__ import annotations

from dataclasses import dataclass

from app.application.suppliers.ports import SupplierRepository
from app.domain.common.errors import ValidationError
from app.domain.suppliers import Supplier


@dataclass(slots=True)
class RegisterSupplierInput:
    name: str
    contact_email: str | None = None
    contact_phone: str | None = None


class RegisterSupplierUseCase:
    def __init__(self, repository: SupplierRepository) -> None:
        self._repository = repository

    async def execute(self, data: RegisterSupplierInput) -> Supplier:
        if not data.name or not data.name.strip():
            raise ValidationError("name is required")

        normalized_email: str | None = None
        if data.contact_email is not None:
            normalized_email = Supplier.normalize_email(data.contact_email)
            existing = await self._repository.get_by_email(normalized_email)
            if existing is not None:
                raise ValidationError("Supplier email already registered")

        supplier = Supplier.register(
            name=data.name,
            contact_email=normalized_email,
            contact_phone=data.contact_phone,
        )

        await self._repository.add(supplier)
        return supplier
