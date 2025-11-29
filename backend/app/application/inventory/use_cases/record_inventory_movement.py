from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.application.catalog.ports import ProductRepository
from app.application.inventory.ports import InventoryMovementRepository
from app.domain.common.errors import NotFoundError
from app.domain.inventory import InventoryMovement, MovementDirection, StockLevel


@dataclass(slots=True)
class RecordInventoryMovementInput:
    product_id: str
    quantity: int
    direction: MovementDirection
    reason: str
    reference: str | None = None
    occurred_at: datetime | None = None


@dataclass(slots=True)
class RecordInventoryMovementOutput:
    movement: InventoryMovement
    stock_level: StockLevel


class RecordInventoryMovementUseCase:
    def __init__(self, product_repo: ProductRepository, inventory_repo: InventoryMovementRepository):
        self._product_repo = product_repo
        self._inventory_repo = inventory_repo

    async def execute(self, data: RecordInventoryMovementInput) -> RecordInventoryMovementOutput:
        product = await self._product_repo.get_by_id(data.product_id)
        if product is None:
            raise NotFoundError("Product not found")

        movement = InventoryMovement.record(
            product_id=product.id,
            quantity=data.quantity,
            direction=data.direction,
            reason=data.reason,
            reference=data.reference,
            occurred_at=data.occurred_at,
        )
        await self._inventory_repo.add(movement)
        stock = await self._inventory_repo.get_stock_level(product.id)
        return RecordInventoryMovementOutput(movement=movement, stock_level=stock)
