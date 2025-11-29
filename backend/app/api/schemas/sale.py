from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Sequence

from pydantic import BaseModel, Field, field_validator

from app.api.schemas.inventory import InventoryMovementOut
from app.domain.inventory import InventoryMovement
from app.domain.sales import Sale, SaleItem


class SaleLineCreate(BaseModel):
    product_id: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(gt=Decimal("0"))


class SaleCreate(BaseModel):
    currency: str = Field(default="USD", min_length=3, max_length=3)
    lines: list[SaleLineCreate]
    customer_id: str | None = Field(default=None, min_length=1, max_length=26)

    @field_validator("lines")
    @classmethod
    def ensure_lines_present(cls, value: list[SaleLineCreate]) -> list[SaleLineCreate]:
        if not value:
            raise ValueError("Sale requires at least one line")
        return value


class SaleItemOut(BaseModel):
    id: str
    product_id: str
    quantity: int
    unit_price: str
    line_total: str

    @classmethod
    def from_domain(cls, item: SaleItem) -> SaleItemOut:
        return cls(
            id=item.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=str(item.unit_price.amount),
            line_total=str(item.line_total.amount),
        )


class SaleOut(BaseModel):
    id: str
    currency: str
    total_amount: str
    total_quantity: int
    created_at: datetime
    closed_at: datetime | None
    items: list[SaleItemOut]
    customer_id: str | None

    @classmethod
    def from_domain(cls, sale: Sale) -> SaleOut:
        return cls(
            id=sale.id,
            currency=sale.currency,
            total_amount=str(sale.total_amount.amount),
            total_quantity=sale.total_quantity,
            created_at=sale.created_at,
            closed_at=sale.closed_at,
            items=[SaleItemOut.from_domain(item) for item in sale.iter_items()],
            customer_id=sale.customer_id,
        )


class SaleRecordOut(BaseModel):
    sale: SaleOut
    movements: list[InventoryMovementOut]

    @classmethod
    def build(cls, sale: Sale, movements: Sequence[InventoryMovement]) -> SaleRecordOut:
        movement_out = [InventoryMovementOut.model_validate(m) for m in movements]
        return cls(sale=SaleOut.from_domain(sale), movements=movement_out)


class SalePageMetaOut(BaseModel):
    page: int
    limit: int
    total: int
    pages: int


class SaleListOut(BaseModel):
    items: list[SaleOut]
    meta: SalePageMetaOut
