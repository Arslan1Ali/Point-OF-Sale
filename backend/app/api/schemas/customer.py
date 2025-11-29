from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.application.customers.use_cases.get_customer_summary import CustomerSummaryResult
from app.domain.customers import Customer
from app.domain.sales import Sale, SaleItem


class CustomerCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, min_length=7, max_length=32)


class CustomerOut(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
    version: int

    model_config = dict(from_attributes=True)

    @classmethod
    def from_domain(cls, customer: Customer) -> CustomerOut:
        return cls(
            id=customer.id,
            first_name=customer.first_name,
            last_name=customer.last_name,
            email=customer.email,
            phone=customer.phone,
            active=customer.active,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
            version=customer.version,
        )


class CustomerPageMetaOut(BaseModel):
    page: int
    limit: int
    total: int
    pages: int


class CustomerListOut(BaseModel):
    items: list[CustomerOut]
    meta: CustomerPageMetaOut


class CustomerDetailOut(CustomerOut):
    full_name: str

    @classmethod
    def from_domain(cls, customer: Customer) -> CustomerDetailOut:
        base = CustomerOut.from_domain(customer)
        return cls(**base.model_dump(), full_name=customer.full_name)


class CustomerUpdate(BaseModel):
    expected_version: int = Field(ge=0)
    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    last_name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=7, max_length=32)


class CustomerDeactivate(BaseModel):
    expected_version: int = Field(ge=0)


class CustomerSaleItemOut(BaseModel):
    product_id: str
    quantity: int
    unit_price: str
    line_total: str

    @classmethod
    def from_domain(cls, item: SaleItem) -> CustomerSaleItemOut:
        return cls(
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=str(item.unit_price.amount),
            line_total=str(item.line_total.amount),
        )


class CustomerSaleOut(BaseModel):
    id: str
    currency: str
    total_amount: str
    total_quantity: int
    created_at: datetime
    closed_at: datetime | None
    items: list[CustomerSaleItemOut]

    @classmethod
    def from_domain(cls, sale: Sale) -> CustomerSaleOut:
        return cls(
            id=sale.id,
            currency=sale.currency,
            total_amount=str(sale.total_amount.amount),
            total_quantity=sale.total_quantity,
            created_at=sale.created_at,
            closed_at=sale.closed_at,
            items=[CustomerSaleItemOut.from_domain(item) for item in sale.iter_items()],
        )


class CustomerSalesListOut(BaseModel):
    items: list[CustomerSaleOut]
    meta: CustomerPageMetaOut


class CustomerSummaryOut(BaseModel):
    customer_id: str
    currency: str | None
    total_sales: int
    total_quantity: int
    lifetime_value: str
    average_order_value: str | None
    first_purchase_at: datetime | None
    last_purchase_at: datetime | None
    last_sale_id: str | None
    last_sale_amount: str | None

    @classmethod
    def from_result(cls, result: CustomerSummaryResult) -> CustomerSummaryOut:
        def _fmt(value: Decimal | None) -> str | None:
            if value is None:
                return None
            return format(value, "0.2f")

        return cls(
            customer_id=result.customer_id,
            currency=result.currency,
            total_sales=result.total_sales,
            total_quantity=result.total_quantity,
            lifetime_value=format(result.total_amount, "0.2f"),
            average_order_value=_fmt(result.average_order_value),
            first_purchase_at=result.first_purchase_at,
            last_purchase_at=result.last_purchase_at,
            last_sale_id=result.last_sale_id,
            last_sale_amount=_fmt(result.last_sale_amount),
        )
