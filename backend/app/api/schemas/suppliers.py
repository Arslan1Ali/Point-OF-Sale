from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.application.suppliers.use_cases.get_supplier_summary import SupplierSummaryResult
from app.domain.suppliers import Supplier


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    contact_email: str | None = Field(default=None, max_length=255)
    contact_phone: str | None = Field(default=None, max_length=32)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = " ".join(part for part in value.strip().split() if part)
        if not normalized:
            raise ValueError("name is required")
        return normalized


class SupplierOut(BaseModel):
    id: str
    name: str
    contact_email: str | None
    contact_phone: str | None
    active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, supplier: Supplier) -> SupplierOut:
        return cls(
            id=supplier.id,
            name=supplier.name,
            contact_email=supplier.contact_email,
            contact_phone=supplier.contact_phone,
            active=supplier.active,
            created_at=supplier.created_at,
            updated_at=supplier.updated_at,
        )


class SupplierDetailOut(SupplierOut):
    @classmethod
    def from_domain(cls, supplier: Supplier) -> SupplierDetailOut:
        base = SupplierOut.from_domain(supplier)
        return cls(**base.model_dump())


class SupplierPageMetaOut(BaseModel):
    page: int
    limit: int
    total: int
    pages: int


class SupplierListOut(BaseModel):
    items: list[SupplierOut]
    meta: SupplierPageMetaOut


class SupplierSummaryOut(BaseModel):
    supplier_id: str
    currency: str | None
    total_orders: int
    total_quantity: int
    total_amount: str
    average_order_value: str | None
    average_lead_time_hours: str | None
    first_order_at: datetime | None
    last_order_at: datetime | None
    last_order_id: str | None
    last_order_amount: str | None
    open_orders: int

    @classmethod
    def from_result(cls, result: SupplierSummaryResult) -> SupplierSummaryOut:
        def _fmt(value: Decimal | None) -> str | None:
            if value is None:
                return None
            return format(value, "0.2f")

        return cls(
            supplier_id=result.supplier_id,
            currency=result.currency,
            total_orders=result.total_orders,
            total_quantity=result.total_quantity,
            total_amount=format(result.total_amount, "0.2f"),
            average_order_value=_fmt(result.average_order_value),
            average_lead_time_hours=_fmt(result.average_lead_time_hours),
            first_order_at=result.first_order_at,
            last_order_at=result.last_order_at,
            last_order_id=result.last_order_id,
            last_order_amount=_fmt(result.last_order_amount),
            open_orders=result.open_orders,
        )
