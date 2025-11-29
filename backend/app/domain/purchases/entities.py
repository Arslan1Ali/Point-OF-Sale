from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from app.domain.common.errors import ValidationError
from app.domain.common.identifiers import new_ulid
from app.domain.common.money import Money


@dataclass(slots=True)
class PurchaseOrderItem:
    id: str
    product_id: str
    quantity: int
    unit_cost: Money
    line_total: Money

    @staticmethod
    def create(
        *,
        product_id: str,
        quantity: int,
        unit_cost: Decimal,
        currency: str,
    ) -> PurchaseOrderItem:
        if not product_id:
            raise ValidationError("product_id is required", code="purchase_item.invalid_product_id")
        if quantity <= 0:
            raise ValidationError("quantity must be positive", code="purchase_item.invalid_quantity")
        if unit_cost <= Decimal("0"):
            raise ValidationError("unit_cost must be positive", code="purchase_item.invalid_unit_cost")

        price = Money(unit_cost, currency)
        return PurchaseOrderItem(
            id=new_ulid(),
            product_id=product_id,
            quantity=quantity,
            unit_cost=price,
            line_total=price.multiply(quantity),
        )


@dataclass(slots=True)
class PurchaseOrder:
    id: str
    supplier_id: str
    currency: str
    items: list[PurchaseOrderItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    received_at: datetime | None = None

    @staticmethod
    def start(*, supplier_id: str, currency: str = "USD") -> PurchaseOrder:
        if not supplier_id:
            raise ValidationError("supplier_id is required", code="purchase.invalid_supplier_id")
        if not currency or len(currency) != 3:
            raise ValidationError("currency must be a 3-letter code", code="purchase.invalid_currency")
        return PurchaseOrder(id=new_ulid(), supplier_id=supplier_id, currency=currency.upper())

    def add_item(self, item: PurchaseOrderItem) -> None:
        if item.unit_cost.currency != self.currency:
            raise ValidationError("item currency mismatch", code="purchase.currency_mismatch")
        self.items.append(item)

    def add_line(
        self,
        *,
        product_id: str,
        quantity: int,
        unit_cost: Decimal,
    ) -> PurchaseOrderItem:
        item = PurchaseOrderItem.create(
            product_id=product_id,
            quantity=quantity,
            unit_cost=unit_cost,
            currency=self.currency,
        )
        self.add_item(item)
        return item

    @property
    def total_amount(self) -> Money:
        total = Money(Decimal("0"), self.currency)
        for item in self.items:
            total = total.add(item.line_total)
        return total

    @property
    def total_quantity(self) -> int:
        return sum(item.quantity for item in self.items)

    def iter_items(self) -> Iterable[PurchaseOrderItem]:
        return iter(self.items)
