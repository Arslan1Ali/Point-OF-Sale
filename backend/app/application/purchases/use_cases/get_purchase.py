from __future__ import annotations

from dataclasses import dataclass

from app.application.purchases.ports import PurchaseRepository
from app.domain.common.errors import NotFoundError
from app.domain.purchases import PurchaseOrder


@dataclass(slots=True)
class GetPurchaseInput:
    purchase_id: str


class GetPurchaseUseCase:
    def __init__(self, repo: PurchaseRepository) -> None:
        self._repo = repo

    async def execute(self, data: GetPurchaseInput) -> PurchaseOrder:
        purchase = await self._repo.get_purchase(data.purchase_id)
        if purchase is None:
            raise NotFoundError("Purchase not found")
        return purchase
