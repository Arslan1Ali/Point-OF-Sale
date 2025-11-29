from __future__ import annotations

from dataclasses import dataclass

from app.application.customers.ports import CustomerRepository
from app.application.sales.ports import SalesRepository
from app.domain.common.errors import NotFoundError, ValidationError
from app.domain.sales import Sale


@dataclass(slots=True)
class ListCustomerSalesInput:
    customer_id: str
    page: int = 1
    limit: int = 20


@dataclass(slots=True)
class ListCustomerSalesResult:
    sales: list[Sale]
    total: int
    page: int
    limit: int
    pages: int


class ListCustomerSalesUseCase:
    def __init__(self, sales_repo: SalesRepository, customer_repo: CustomerRepository) -> None:
        self._sales_repo = sales_repo
        self._customer_repo = customer_repo

    async def execute(self, data: ListCustomerSalesInput) -> ListCustomerSalesResult:
        if data.page < 1:
            raise ValidationError("page must be >= 1")
        if data.limit < 1 or data.limit > 100:
            raise ValidationError("limit must be between 1 and 100")

        customer = await self._customer_repo.get_by_id(data.customer_id)
        if customer is None:
            raise NotFoundError("Customer not found")

        offset = (data.page - 1) * data.limit
        sales, total = await self._sales_repo.list_sales_for_customer(
            data.customer_id,
            offset=offset,
            limit=data.limit,
        )
        pages = (total + data.limit - 1) // data.limit if total > 0 else 0
        return ListCustomerSalesResult(
            sales=list(sales),
            total=total,
            page=data.page,
            limit=data.limit,
            pages=pages,
        )
