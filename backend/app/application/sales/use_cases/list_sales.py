from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.application.sales.ports import SalesRepository
from app.domain.common.errors import ValidationError
from app.domain.sales import Sale


@dataclass(slots=True)
class ListSalesInput:
    page: int = 1
    limit: int = 20
    customer_id: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


@dataclass(slots=True)
class ListSalesResult:
    sales: list[Sale]
    total: int
    page: int
    limit: int
    pages: int


class ListSalesUseCase:
    def __init__(self, sales_repo: SalesRepository) -> None:
        self._sales_repo = sales_repo

    async def execute(self, data: ListSalesInput) -> ListSalesResult:
        if data.page < 1:
            raise ValidationError("page must be >= 1")
        if data.limit < 1 or data.limit > 100:
            raise ValidationError("limit must be between 1 and 100")
        if data.date_from is not None and data.date_to is not None and data.date_from > data.date_to:
            raise ValidationError("date_from must be before or equal to date_to")

        offset = (data.page - 1) * data.limit
        sales, total = await self._sales_repo.list_sales(
            customer_id=data.customer_id,
            date_from=data.date_from,
            date_to=data.date_to,
            offset=offset,
            limit=data.limit,
        )
        pages = (total + data.limit - 1) // data.limit if total > 0 else 0
        return ListSalesResult(sales=list(sales), total=total, page=data.page, limit=data.limit, pages=pages)
