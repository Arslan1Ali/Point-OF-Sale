from __future__ import annotations

from dataclasses import dataclass

from app.application.customers.ports import CustomerRepository
from app.domain.common.errors import ConflictError, NotFoundError, ValidationError
from app.domain.customers import Customer


@dataclass(slots=True)
class DeactivateCustomerInput:
    customer_id: str
    expected_version: int


class DeactivateCustomerUseCase:
    def __init__(self, repo: CustomerRepository) -> None:
        self._repo = repo

    async def execute(self, data: DeactivateCustomerInput) -> Customer:
        customer = await self._repo.get_by_id(data.customer_id)
        if customer is None:
            raise NotFoundError("Customer not found")
        if customer.version != data.expected_version:
            raise ConflictError("Customer was modified by another transaction")

        changed = customer.deactivate()
        if not changed:
            raise ValidationError("Customer already inactive")

        success = await self._repo.update(customer, expected_version=data.expected_version)
        if not success:
            raise ConflictError("Customer was modified by another transaction")
        return customer
