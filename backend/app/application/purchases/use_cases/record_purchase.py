from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from app.application.catalog.ports import ProductRepository
from app.application.inventory.ports import InventoryMovementRepository
from app.application.purchases.ports import PurchaseRepository
from app.application.suppliers.ports import SupplierRepository
from app.domain.catalog.entities import Product
from app.domain.common.errors import NotFoundError, ValidationError
from app.domain.inventory import InventoryMovement, MovementDirection
from app.domain.purchases import PurchaseOrder


@dataclass(slots=True)
class PurchaseLineInput:
    product_id: str
    quantity: int
    unit_cost: Decimal


@dataclass(slots=True)
class RecordPurchaseInput:
    supplier_id: str
    lines: Sequence[PurchaseLineInput]
    currency: str = "USD"


@dataclass(slots=True)
class RecordPurchaseResult:
    purchase: PurchaseOrder
    movements: list[InventoryMovement]


class RecordPurchaseUseCase:
    def __init__(
        self,
        supplier_repo: SupplierRepository,
        product_repo: ProductRepository,
        purchase_repo: PurchaseRepository,
        inventory_repo: InventoryMovementRepository,
    ) -> None:
        self._supplier_repo = supplier_repo
        self._product_repo = product_repo
        self._purchase_repo = purchase_repo
        self._inventory_repo = inventory_repo

    async def execute(self, data: RecordPurchaseInput) -> RecordPurchaseResult:
        if not data.supplier_id or not data.supplier_id.strip():
            raise ValidationError("supplier_id is required")
        if not data.lines:
            raise ValidationError("Purchase requires at least one line item")

        supplier = await self._supplier_repo.get_by_id(data.supplier_id)
        if supplier is None:
            raise NotFoundError("Supplier not found")
        if not supplier.active:
            raise ValidationError("Supplier is inactive")

        purchase = PurchaseOrder.start(supplier_id=supplier.id, currency=data.currency)
        purchase.received_at = purchase.created_at
        product_cache: dict[str, Product] = {}

        for line in data.lines:
            if not line.product_id or not line.product_id.strip():
                raise ValidationError("product_id is required")
            if line.quantity <= 0:
                raise ValidationError("Quantity must be positive")
            if line.unit_cost <= Decimal("0"):
                raise ValidationError("Unit cost must be positive")

            product = product_cache.get(line.product_id)
            if product is None:
                product = await self._product_repo.get_by_id(line.product_id)
                if product is None:
                    raise NotFoundError(f"Product {line.product_id} not found")
                if not product.active:
                    raise ValidationError(f"Product {product.id} is inactive")
                product_cache[line.product_id] = product

            purchase.add_line(
                product_id=product.id,
                quantity=line.quantity,
                unit_cost=line.unit_cost,
            )

        await self._purchase_repo.add_purchase(purchase, list(purchase.iter_items()))

        movements: list[InventoryMovement] = []
        for item in purchase.iter_items():
            movement = InventoryMovement.record(
                product_id=item.product_id,
                quantity=item.quantity,
                direction=MovementDirection.IN,
                reason="purchase",
                reference=purchase.id,
                occurred_at=purchase.created_at,
            )
            await self._inventory_repo.add(movement)
            movements.append(movement)

        return RecordPurchaseResult(purchase=purchase, movements=movements)
