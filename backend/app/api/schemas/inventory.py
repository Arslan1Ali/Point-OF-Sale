from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.inventory import MovementDirection


class InventoryMovementCreate(BaseModel):
    quantity: int = Field(gt=0)
    direction: MovementDirection
    reason: str = Field(min_length=1, max_length=128)
    reference: str | None = Field(default=None, max_length=128)
    occurred_at: datetime | None = None


class InventoryMovementOut(BaseModel):
    id: str
    product_id: str
    quantity: int
    direction: MovementDirection
    reason: str
    reference: str | None
    occurred_at: datetime
    created_at: datetime

    model_config = dict(from_attributes=True)


class StockLevelOut(BaseModel):
    product_id: str
    quantity_on_hand: int
    as_of: datetime

    model_config = dict(from_attributes=True)


class InventoryMovementRecordOut(BaseModel):
    movement: InventoryMovementOut
    stock: StockLevelOut


class InventoryMovementPageMetaOut(BaseModel):
    page: int
    limit: int
    total: int
    pages: int


class InventoryMovementListOut(BaseModel):
    items: list[InventoryMovementOut]
    meta: InventoryMovementPageMetaOut
