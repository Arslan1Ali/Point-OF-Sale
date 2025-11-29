from __future__ import annotations

from dataclasses import dataclass

from app.application.customers.ports import CustomerRepository
from app.domain.common.errors import NotFoundError
from app.domain.customers import Customer


@dataclass(slots=True)
class GetCustomerInput:
    customer_id: str


class GetCustomerUseCase:
    def __init__(self, repo: CustomerRepository) -> None:
        self._repo = repo

    async def execute(self, data: GetCustomerInput) -> Customer:
        customer = await self._repo.get_by_id(data.customer_id)
        if customer is None:
            raise NotFoundError(f"Customer {data.customer_id} not found")
        return customer
