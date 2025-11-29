from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Sequence

from app.application.inventory.ports import InventoryMovementRepository
from app.application.returns.ports import ReturnsRepository
from app.application.sales.ports import SalesRepository
from app.domain.common.errors import NotFoundError, ValidationError
from app.domain.inventory import InventoryMovement, MovementDirection
from app.domain.returns import Return


@dataclass(slots=True)
class ReturnLineInput:
    sale_item_id: str
    quantity: int


@dataclass(slots=True)
class RecordReturnInput:
    sale_id: str
    lines: Sequence[ReturnLineInput]


@dataclass(slots=True)
class RecordReturnResult:
    return_: Return
    movements: list[InventoryMovement]


class RecordReturnUseCase:
    def __init__(
        self,
        sales_repo: SalesRepository,
        returns_repo: ReturnsRepository,
        inventory_repo: InventoryMovementRepository,
    ) -> None:
        self._sales_repo = sales_repo
        self._returns_repo = returns_repo
        self._inventory_repo = inventory_repo

    async def execute(self, data: RecordReturnInput) -> RecordReturnResult:
        if not data.sale_id:
            raise ValidationError("sale_id is required")
        if not data.lines:
            raise ValidationError("Return requires at least one line item")

        sale = await self._sales_repo.get_by_id(data.sale_id)
        if sale is None:
            raise NotFoundError("Sale not found")
        if not sale.is_closed:
            raise ValidationError("Return can only be recorded for closed sales")

        sale_items = {item.id: item for item in sale.iter_items()}
        if not sale_items:
            raise ValidationError("Sale has no items to return")

        aggregated: OrderedDict[str, int] = OrderedDict()
        for line in data.lines:
            sale_item_id = line.sale_item_id.strip() if line.sale_item_id else ""
            if not sale_item_id:
                raise ValidationError("sale_item_id is required")
            if line.quantity <= 0:
                raise ValidationError("Return quantity must be positive")
            if sale_item_id not in sale_items:
                raise ValidationError(f"Sale item {sale_item_id} not found on sale")
            aggregated[sale_item_id] = aggregated.get(sale_item_id, 0) + line.quantity

        prior_quantities = await self._returns_repo.get_returned_quantities(list(aggregated.keys()))

        for sale_item_id, requested_qty in aggregated.items():
            sale_item = sale_items[sale_item_id]
            already_returned = int(prior_quantities.get(sale_item_id, 0))
            remaining = sale_item.quantity - already_returned
            if requested_qty > remaining:
                raise ValidationError(
                    f"Return quantity exceeds remaining for sale item {sale_item_id}",
                )

        return_ = Return.start(sale_id=sale.id, currency=sale.currency)
        movements: list[InventoryMovement] = []
        for sale_item_id, quantity in aggregated.items():
            sale_item = sale_items[sale_item_id]
            return_.add_line(
                sale_item_id=sale_item_id,
                product_id=sale_item.product_id,
                quantity=quantity,
                unit_price=sale_item.unit_price.amount,
            )

        await self._returns_repo.add_return(return_, list(return_.iter_items()))

        for item in return_.iter_items():
            movement = InventoryMovement.record(
                product_id=item.product_id,
                quantity=item.quantity,
                direction=MovementDirection.IN,
                reason="return",
                reference=return_.id,
                occurred_at=return_.created_at,
            )
            await self._inventory_repo.add(movement)
            movements.append(movement)

        return RecordReturnResult(return_=return_, movements=movements)
