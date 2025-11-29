from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.application.purchases.ports import PurchaseRepository, SupplierPurchaseSummary
from app.application.suppliers.ports import SupplierRepository
from app.domain.common.errors import NotFoundError


@dataclass(slots=True)
class SupplierSummaryResult:
    supplier_id: str
    currency: str | None
    total_orders: int
    total_amount: Decimal
    total_quantity: int
    first_order_at: datetime | None
    last_order_at: datetime | None
    last_order_id: str | None
    last_order_amount: Decimal | None
    average_order_value: Decimal | None
    open_orders: int
    average_lead_time_hours: Decimal | None


class GetSupplierSummaryUseCase:
    def __init__(self, supplier_repo: SupplierRepository, purchase_repo: PurchaseRepository) -> None:
        self._supplier_repo = supplier_repo
        self._purchase_repo = purchase_repo

    async def execute(self, supplier_id: str) -> SupplierSummaryResult:
        supplier = await self._supplier_repo.get_by_id(supplier_id)
        if supplier is None:
            raise NotFoundError("Supplier not found")

        summary: SupplierPurchaseSummary = await self._purchase_repo.get_supplier_purchase_summary(supplier_id)
        average_order_value: Decimal | None = None
        if summary.total_orders > 0:
            average_order_value = (summary.total_amount / Decimal(summary.total_orders)).quantize(Decimal("0.01"))

        return SupplierSummaryResult(
            supplier_id=supplier.id,
            currency=summary.currency,
            total_orders=summary.total_orders,
            total_amount=summary.total_amount,
            total_quantity=summary.total_quantity,
            first_order_at=summary.first_order_at,
            last_order_at=summary.last_order_at,
            last_order_id=summary.last_order_id,
            last_order_amount=summary.last_order_amount,
            average_order_value=average_order_value,
            open_orders=summary.open_orders,
            average_lead_time_hours=summary.average_lead_time_hours,
        )
