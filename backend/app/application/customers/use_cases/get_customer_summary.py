from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.application.customers.ports import CustomerRepository
from app.application.sales.ports import CustomerSalesSummary, SalesRepository
from app.domain.common.errors import NotFoundError


@dataclass(slots=True)
class CustomerSummaryResult:
    customer_id: str
    currency: str | None
    total_sales: int
    total_amount: Decimal
    total_quantity: int
    first_purchase_at: datetime | None
    last_purchase_at: datetime | None
    last_sale_id: str | None
    last_sale_amount: Decimal | None
    average_order_value: Decimal | None


class GetCustomerSummaryUseCase:
    def __init__(self, customer_repo: CustomerRepository, sales_repo: SalesRepository) -> None:
        self._customer_repo = customer_repo
        self._sales_repo = sales_repo

    async def execute(self, customer_id: str) -> CustomerSummaryResult:
        customer = await self._customer_repo.get_by_id(customer_id)
        if customer is None:
            raise NotFoundError("Customer not found")

        summary: CustomerSalesSummary = await self._sales_repo.get_customer_sales_summary(customer_id)
        average_order_value: Decimal | None = None
        if summary.total_sales > 0:
            average_order_value = (summary.total_amount / Decimal(summary.total_sales)).quantize(
                Decimal("0.01")
            )

        return CustomerSummaryResult(
            customer_id=customer.id,
            currency=summary.currency,
            total_sales=summary.total_sales,
            total_amount=summary.total_amount,
            total_quantity=summary.total_quantity,
            first_purchase_at=summary.first_sale_at,
            last_purchase_at=summary.last_sale_at,
            last_sale_id=summary.last_sale_id,
            last_sale_amount=summary.last_sale_amount,
            average_order_value=average_order_value,
        )
