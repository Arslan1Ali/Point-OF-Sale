from __future__ import annotations

from dataclasses import dataclass

from app.application.customers.ports import CustomerRepository
from app.domain.common.errors import ValidationError
from app.domain.customers import Customer


@dataclass(slots=True)
class ListCustomersInput:
    page: int = 1
    limit: int = 20
    search: str | None = None
    active: bool | None = None


@dataclass(slots=True)
class ListCustomersResult:
    customers: list[Customer]
    total: int
    page: int
    limit: int
    pages: int


class ListCustomersUseCase:
    def __init__(self, repo: CustomerRepository) -> None:
        self._repo = repo

    async def execute(self, data: ListCustomersInput) -> ListCustomersResult:
        if data.page < 1:
            raise ValidationError("page must be >= 1")
        if data.limit < 1 or data.limit > 100:
            raise ValidationError("limit must be between 1 and 100")

        offset = (data.page - 1) * data.limit
        customers, total = await self._repo.list_customers(
            search=data.search,
            active=data.active,
            offset=offset,
            limit=data.limit,
        )
        pages = (total + data.limit - 1) // data.limit if total > 0 else 0
        return ListCustomersResult(
            customers=list(customers),
            total=total,
            page=data.page,
            limit=data.limit,
            pages=pages,
        )
