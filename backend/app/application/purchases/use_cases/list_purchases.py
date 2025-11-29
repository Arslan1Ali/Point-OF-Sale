from __future__ import annotations

from dataclasses import dataclass

from app.application.purchases.ports import PurchaseRepository
from app.domain.common.errors import ValidationError
from app.domain.purchases import PurchaseOrder


@dataclass(slots=True)
class ListPurchasesInput:
    page: int = 1
    limit: int = 20
    supplier_id: str | None = None


@dataclass(slots=True)
class ListPurchasesResult:
    purchases: list[PurchaseOrder]
    total: int
    page: int
    limit: int
    pages: int


class ListPurchasesUseCase:
    def __init__(self, repo: PurchaseRepository) -> None:
        self._repo = repo

    async def execute(self, data: ListPurchasesInput) -> ListPurchasesResult:
        if data.page < 1:
            raise ValidationError("page must be >= 1")
        if data.limit < 1 or data.limit > 100:
            raise ValidationError("limit must be between 1 and 100")

        offset = (data.page - 1) * data.limit
        purchases, total = await self._repo.list_purchases(
            supplier_id=data.supplier_id,
            offset=offset,
            limit=data.limit,
        )
        pages = (total + data.limit - 1) // data.limit if total > 0 else 0
        return ListPurchasesResult(
            purchases=list(purchases),
            total=total,
            page=data.page,
            limit=data.limit,
            pages=pages,
        )
