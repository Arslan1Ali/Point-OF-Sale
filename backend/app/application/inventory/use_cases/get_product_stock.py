from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.application.catalog.ports import ProductRepository
from app.application.inventory.ports import InventoryMovementRepository
from app.domain.common.errors import NotFoundError
from app.domain.inventory import StockLevel


@dataclass(slots=True)
class GetProductStockInput:
    product_id: str
    as_of: datetime | None = None


class GetProductStockUseCase:
    def __init__(self, product_repo: ProductRepository, inventory_repo: InventoryMovementRepository):
        self._product_repo = product_repo
        self._inventory_repo = inventory_repo

    async def execute(self, data: GetProductStockInput) -> StockLevel:
        product = await self._product_repo.get_by_id(data.product_id)
        if product is None:
            raise NotFoundError("Product not found")
        return await self._inventory_repo.get_stock_level(product.id, as_of=data.as_of)
