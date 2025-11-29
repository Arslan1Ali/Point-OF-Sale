from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from app.domain.common.errors import ValidationError
from app.domain.common.identifiers import new_ulid


class MovementDirection(str, Enum):
    IN = "in"
    OUT = "out"


@dataclass(slots=True)
class InventoryMovement:
    id: str
    product_id: str
    quantity: int
    direction: MovementDirection
    reason: str
    reference: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def delta(self) -> int:
        return self.quantity if self.direction == MovementDirection.IN else -self.quantity

    @staticmethod
    def record(
        *,
        product_id: str,
        quantity: int,
        direction: MovementDirection,
        reason: str,
        reference: str | None = None,
        occurred_at: datetime | None = None,
    ) -> InventoryMovement:
        if not product_id:
            raise ValidationError("product_id is required", code="inventory.invalid_product_id")
        if quantity <= 0:
            raise ValidationError("quantity must be positive", code="inventory.invalid_quantity")
        if not reason or not reason.strip():
            raise ValidationError("reason is required", code="inventory.invalid_reason")
        occurred = occurred_at or datetime.now(UTC)
        return InventoryMovement(
            id=new_ulid(),
            product_id=product_id,
            quantity=quantity,
            direction=direction,
            reason=reason.strip(),
            reference=reference.strip() if reference and reference.strip() else None,
            occurred_at=occurred,
        )


@dataclass(slots=True)
class StockLevel:
    product_id: str
    quantity_on_hand: int
    as_of: datetime

    @staticmethod
    def from_movements(
        product_id: str,
        *,
        total_delta: int | None = None,
        movements: Sequence[InventoryMovement] | None = None,
        as_of: datetime | None = None,
    ) -> StockLevel:
        timestamp = _normalize_timestamp(as_of)
        if movements is not None:
            total = compute_total_delta_up_to(movements, as_of=timestamp)
        elif total_delta is not None:
            total = total_delta
        else:
            raise ValidationError("total_delta or movements must be provided", code="inventory.missing_movements")
        return StockLevel(product_id=product_id, quantity_on_hand=total, as_of=timestamp)


def compute_total_delta(movements: Sequence[InventoryMovement]) -> int:
    return sum(movement.delta for movement in movements)


def compute_total_delta_up_to(
    movements: Sequence[InventoryMovement],
    *,
    as_of: datetime | None = None,
) -> int:
    cutoff = _normalize_timestamp(as_of)
    total = 0
    for movement in movements:
        occurred = _normalize_timestamp(movement.occurred_at)
        if occurred <= cutoff:
            total += movement.delta
    return total


def _normalize_timestamp(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
