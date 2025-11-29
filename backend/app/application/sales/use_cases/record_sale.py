from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from app.application.catalog.ports import ProductRepository
from app.application.common.event_dispatcher import EventDispatcher
from app.application.customers.ports import CustomerRepository
from app.application.inventory.ports import InventoryMovementRepository
from app.application.sales.ports import SalesRepository
from app.domain.catalog.entities import Product
from app.domain.common.errors import ConflictError, NotFoundError, ValidationError
from app.domain.inventory import InventoryMovement, MovementDirection
from app.domain.sales import Sale
from app.domain.sales.events import SaleRecordedEvent


@dataclass(slots=True)
class SaleLineInput:
    product_id: str
    quantity: int
    unit_price: Decimal


@dataclass(slots=True)
class RecordSaleInput:
    lines: Sequence[SaleLineInput]
    currency: str = "USD"
    customer_id: str | None = None


@dataclass(slots=True)
class RecordSaleResult:
    sale: Sale
    movements: list[InventoryMovement]


class RecordSaleUseCase:
    def __init__(
        self,
        product_repo: ProductRepository,
        sales_repo: SalesRepository,
        inventory_repo: InventoryMovementRepository,
        customer_repo: CustomerRepository | None = None,
        event_dispatcher: EventDispatcher | None = None,
    ) -> None:
        self._product_repo = product_repo
        self._sales_repo = sales_repo
        self._inventory_repo = inventory_repo
        self._customer_repo = customer_repo
        self._event_dispatcher = event_dispatcher

    async def execute(self, data: RecordSaleInput) -> RecordSaleResult:
        if not data.lines:
            raise ValidationError("Sale requires at least one line item")

        sale = Sale.start(currency=data.currency)
        product_cache: dict[str, Product] = {}
        required_quantities: dict[str, int] = {}

        if data.customer_id is not None:
            if self._customer_repo is None:
                raise ValidationError("Customer support is not configured")
            customer = await self._customer_repo.get_by_id(data.customer_id)
            if customer is None:
                raise NotFoundError("Customer not found")
            if not customer.active:
                raise ValidationError("Customer is inactive")
            sale.assign_customer(customer.id)

        # Pre-fetch and lock products in deterministic order to prevent deadlocks
        unique_product_ids = sorted(list(set(line.product_id for line in data.lines)))
        for pid in unique_product_ids:
            product = await self._product_repo.get_by_id(pid, lock=True)
            if product is None:
                raise NotFoundError(f"Product {pid} not found")
            if not product.active:
                raise ValidationError(f"Product {product.id} is inactive")
            
            # Optimistic locking: touch the product to ensure serialization
            # This works on SQLite (write lock) and Postgres (version check)
            current_version = product.version
            product.version += 1
            success = await self._product_repo.update(product, expected_version=current_version)
            if not success:
                raise ConflictError(f"Product {pid} was modified concurrently")

            product_cache[pid] = product

        for line in data.lines:
            if line.quantity <= 0:
                raise ValidationError("Quantity must be positive")
            if line.unit_price <= Decimal("0"):
                raise ValidationError("Unit price must be positive")

            product = product_cache[line.product_id]
            sale.add_line(product_id=product.id, quantity=line.quantity, unit_price=line.unit_price)
            required_quantities[product.id] = required_quantities.get(product.id, 0) + line.quantity

        for product_id, required in required_quantities.items():
            stock = await self._inventory_repo.get_stock_level(product_id)
            if stock.quantity_on_hand < required:
                raise ValidationError(f"Insufficient stock for product {product_id}")

        sale.close()

        movements: list[InventoryMovement] = []
        for item in sale.iter_items():
            movement = InventoryMovement.record(
                product_id=item.product_id,
                quantity=item.quantity,
                direction=MovementDirection.OUT,
                reason="sale",
                reference=sale.id,
                occurred_at=sale.closed_at,
            )
            await self._inventory_repo.add(movement)
            movements.append(movement)

        await self._sales_repo.add_sale(sale, list(sale.iter_items()))

        if self._event_dispatcher is not None:
            event = SaleRecordedEvent(
                aggregate_id=sale.id,
                total_amount=str(sale.total_amount.amount),
                currency=sale.currency,
                customer_id=sale.customer_id,
            )
            await self._event_dispatcher.publish(event)

        return RecordSaleResult(sale=sale, movements=movements)
