from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol, Sequence

from app.domain.purchases import PurchaseOrder, PurchaseOrderItem


@dataclass(slots=True)
class SupplierPurchaseSummary:
    currency: str | None
    total_orders: int
    total_amount: Decimal
    total_quantity: int
    first_order_at: datetime | None
    last_order_at: datetime | None
    last_order_id: str | None
    last_order_amount: Decimal | None
    open_orders: int
    average_lead_time_hours: Decimal | None


class PurchaseRepository(Protocol):
    async def add_purchase(
        self,
        order: PurchaseOrder,
        items: Sequence[PurchaseOrderItem],
    ) -> None: ...  # pragma: no cover

    async def get_purchase(self, purchase_id: str) -> PurchaseOrder | None: ...  # pragma: no cover

    async def list_purchases(
        self,
        *,
        supplier_id: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[PurchaseOrder], int]: ...  # pragma: no cover

    async def get_supplier_purchase_summary(self, supplier_id: str) -> SupplierPurchaseSummary: ...  # pragma: no cover
