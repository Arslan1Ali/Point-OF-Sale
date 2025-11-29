from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    sku: str = Field(min_length=1, max_length=64)
    retail_price: Decimal = Field(gt=0)
    purchase_price: Decimal = Field(ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    category_id: str | None = None


class ProductOut(BaseModel):
    id: str
    name: str
    sku: str
    retail_price: Decimal
    purchase_price: Decimal
    category_id: str | None
    active: bool
    version: int

    model_config = dict(from_attributes=True)


class ProductUpdate(BaseModel):
    expected_version: int = Field(ge=0)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    retail_price: Decimal | None = Field(default=None, gt=0)
    purchase_price: Decimal | None = Field(default=None, ge=0)
    category_id: str | None = None


class ProductDeactivate(BaseModel):
    expected_version: int = Field(ge=0)
