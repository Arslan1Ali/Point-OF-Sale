from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from app.domain.common.errors import ValidationError
from app.domain.common.identifiers import new_ulid
from app.domain.common.money import Money


@dataclass(slots=True)
class ReturnItem:
    id: str
    sale_item_id: str
    product_id: str
    quantity: int
    unit_price: Money
    line_total: Money

    @staticmethod
    def create(
        *,
        sale_item_id: str,
        product_id: str,
        quantity: int,
        unit_price: Decimal,
        currency: str,
    ) -> ReturnItem:
        if not sale_item_id:
            raise ValidationError("sale_item_id is required", code="return_item.invalid_sale_item_id")
        if not product_id:
            raise ValidationError("product_id is required", code="return_item.invalid_product_id")
        if quantity <= 0:
            raise ValidationError("quantity must be positive", code="return_item.invalid_quantity")
        if unit_price <= Decimal("0"):
            raise ValidationError("unit_price must be positive", code="return_item.invalid_unit_price")

        price = Money(unit_price, currency)
        return ReturnItem(
            id=new_ulid(),
            sale_item_id=sale_item_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=price,
            line_total=price.multiply(quantity),
        )


@dataclass(slots=True)
class Return:
    id: str
    sale_id: str
    currency: str
    items: list[ReturnItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @staticmethod
    def start(*, sale_id: str, currency: str = "USD") -> Return:
        if not sale_id:
            raise ValidationError("sale_id is required", code="return.invalid_sale_id")
        if not currency or len(currency) != 3:
            raise ValidationError("currency must be a 3-letter code", code="return.invalid_currency")
        return Return(id=new_ulid(), sale_id=sale_id, currency=currency.upper())

    def add_item(self, item: ReturnItem) -> None:
        if item.unit_price.currency != self.currency:
            raise ValidationError("item currency mismatch", code="return.currency_mismatch")
        self.items.append(item)

    def add_line(
        self,
        *,
        sale_item_id: str,
        product_id: str,
        quantity: int,
        unit_price: Decimal,
    ) -> ReturnItem:
        item = ReturnItem.create(
            sale_item_id=sale_item_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
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

    def iter_items(self) -> Iterable[ReturnItem]:
        return iter(self.items)
