from __future__ import annotations

from dataclasses import dataclass

from app.application.customers.ports import CustomerRepository
from app.domain.common.errors import ConflictError, NotFoundError, ValidationError
from app.domain.customers import Customer


@dataclass(slots=True)
class UpdateCustomerInput:
    customer_id: str
    expected_version: int
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    first_name_provided: bool = False
    last_name_provided: bool = False
    email_provided: bool = False
    phone_provided: bool = False


class UpdateCustomerUseCase:
    def __init__(self, repo: CustomerRepository) -> None:
        self._repo = repo

    async def execute(self, data: UpdateCustomerInput) -> Customer:
        customer = await self._repo.get_by_id(data.customer_id)
        if customer is None:
            raise NotFoundError("Customer not found")
        if customer.version != data.expected_version:
            raise ConflictError("Customer was modified by another transaction")

        email_to_check: str | None = None
        if data.email_provided:
            if data.email is None:
                raise ValidationError("email is required")
            email_to_check = Customer.normalize_email(data.email)
            existing = await self._repo.get_by_email(email_to_check)
            if existing is not None and existing.id != customer.id:
                raise ConflictError("Customer with this email already exists")

        changed = False
        if data.first_name_provided or data.last_name_provided:
            renamed = customer.rename(
                first_name=data.first_name if data.first_name_provided else None,
                last_name=data.last_name if data.last_name_provided else None,
            )
            changed = changed or renamed
        if data.email_provided or data.phone_provided:
            updated_contact = customer.update_contact(
                email=email_to_check if data.email_provided else None,
                phone=data.phone if data.phone_provided else None,
            )
            changed = changed or updated_contact

        if not changed:
            raise ValidationError("No changes detected")

        success = await self._repo.update(customer, expected_version=data.expected_version)
        if not success:
            raise ConflictError("Customer was modified by another transaction")
        return customer
