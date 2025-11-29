from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol, Sequence

from app.domain.sales import Sale, SaleItem


@dataclass(slots=True)
class CustomerSalesSummary:
    currency: str | None
    total_sales: int
    total_amount: Decimal
    total_quantity: int
    first_sale_at: datetime | None
    last_sale_at: datetime | None
    last_sale_id: str | None
    last_sale_amount: Decimal | None


class SalesRepository(Protocol):
    async def add_sale(self, sale: Sale, items: Sequence[SaleItem]) -> None: ...  # pragma: no cover

    async def get_by_id(self, sale_id: str) -> Sale | None: ...  # pragma: no cover

    async def list_sales(
        self,
        *,
        customer_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Sale], int]: ...  # pragma: no cover

    async def list_sales_for_customer(
        self,
        customer_id: str,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Sale], int]: ...  # pragma: no cover

    async def get_customer_sales_summary(self, customer_id: str) -> CustomerSalesSummary: ...  # pragma: no cover
