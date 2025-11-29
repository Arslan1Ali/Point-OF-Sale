from __future__ import annotations

from datetime import datetime
from typing import Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.schemas.inventory import InventoryMovementOut
from app.domain.inventory import InventoryMovement
from app.domain.returns import Return, ReturnItem


class ReturnLineCreate(BaseModel):
    sale_item_id: str = Field(min_length=1, max_length=26)
    quantity: int = Field(gt=0)


class ReturnCreate(BaseModel):
    sale_id: str = Field(min_length=1, max_length=26)
    lines: list[ReturnLineCreate]

    @field_validator("lines")
    @classmethod
    def ensure_lines_present(cls, value: list[ReturnLineCreate]) -> list[ReturnLineCreate]:
        if not value:
            raise ValueError("Return requires at least one line")
        return value


class ReturnItemOut(BaseModel):
    id: str
    sale_item_id: str
    product_id: str
    quantity: int
    unit_price: str
    line_total: str

    @classmethod
    def from_domain(cls, item: ReturnItem) -> ReturnItemOut:
        return cls(
            id=item.id,
            sale_item_id=item.sale_item_id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=str(item.unit_price.amount),
            line_total=str(item.line_total.amount),
        )


class ReturnOut(BaseModel):
    id: str
    sale_id: str
    currency: str
    total_amount: str
    total_quantity: int
    created_at: datetime
    items: list[ReturnItemOut]

    @classmethod
    def from_domain(cls, return_: Return) -> ReturnOut:
        return cls(
            id=return_.id,
            sale_id=return_.sale_id,
            currency=return_.currency,
            total_amount=str(return_.total_amount.amount),
            total_quantity=return_.total_quantity,
            created_at=return_.created_at,
            items=[ReturnItemOut.from_domain(item) for item in return_.iter_items()],
        )


class ReturnRecordOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    return_: ReturnOut = Field(alias="return")
    movements: list[InventoryMovementOut]

    @classmethod
    def build(cls, return_: Return, movements: Sequence[InventoryMovement]) -> ReturnRecordOut:
        movement_out = [InventoryMovementOut.model_validate(movement) for movement in movements]
        payload = {
            "return": ReturnOut.from_domain(return_),
            "movements": movement_out,
        }
        return cls.model_validate(payload)


class ReturnSummaryOut(BaseModel):
    id: str
    sale_id: str
    currency: str
    total_amount: str
    total_quantity: int
    created_at: datetime

    @classmethod
    def from_domain(cls, return_: Return) -> ReturnSummaryOut:
        return cls(
            id=return_.id,
            sale_id=return_.sale_id,
            currency=return_.currency,
            total_amount=str(return_.total_amount.amount),
            total_quantity=return_.total_quantity,
            created_at=return_.created_at,
        )


class ReturnPageMetaOut(BaseModel):
    page: int
    limit: int
    total: int
    pages: int


class ReturnListOut(BaseModel):
    items: list[ReturnSummaryOut]
    meta: ReturnPageMetaOut
