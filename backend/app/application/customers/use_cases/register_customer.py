from __future__ import annotations

from dataclasses import dataclass

from app.application.customers.ports import CustomerRepository
from app.domain.common.errors import ConflictError, ValidationError
from app.domain.customers import Customer


@dataclass(slots=True)
class RegisterCustomerInput:
    first_name: str
    last_name: str
    email: str
    phone: str | None = None


class RegisterCustomerUseCase:
    def __init__(self, repo: CustomerRepository) -> None:
        self._repo = repo

    async def execute(self, data: RegisterCustomerInput) -> Customer:
        customer = Customer.register(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
        )

        existing = await self._repo.get_by_email(customer.email)
        if existing is not None:
            raise ConflictError("Customer with this email already exists")

        await self._repo.add(customer)
        return customer
