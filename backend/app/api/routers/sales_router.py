from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import SALES_ROLES, require_roles
from app.api.schemas.sale import SaleCreate, SaleListOut, SaleOut, SalePageMetaOut, SaleRecordOut
from app.application.sales.use_cases.get_sale import GetSaleInput, GetSaleUseCase
from app.application.sales.use_cases.list_sales import ListSalesInput, ListSalesUseCase
from app.application.sales.use_cases.record_sale import (
    RecordSaleInput,
    RecordSaleUseCase,
    SaleLineInput,
)
from app.domain.auth.entities import User, UserRole
from app.infrastructure.db.repositories.customer_repository import SqlAlchemyCustomerRepository
from app.infrastructure.db.repositories.inventory_movement_repository import (
    SqlAlchemyInventoryMovementRepository,
)
from app.infrastructure.db.repositories.inventory_repository import SqlAlchemyProductRepository
from app.infrastructure.db.repositories.sales_repository import SqlAlchemySalesRepository
from app.infrastructure.db.session import get_session

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("", response_model=SaleRecordOut, status_code=status.HTTP_201_CREATED)
async def record_sale(
    payload: SaleCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*SALES_ROLES)),
) -> SaleRecordOut:
    product_repo = SqlAlchemyProductRepository(session)
    sales_repo = SqlAlchemySalesRepository(session)
    inventory_repo = SqlAlchemyInventoryMovementRepository(session)
    customer_repo = SqlAlchemyCustomerRepository(session)
    use_case = RecordSaleUseCase(product_repo, sales_repo, inventory_repo, customer_repo)
    result = await use_case.execute(
        RecordSaleInput(
            currency=payload.currency,
            customer_id=payload.customer_id,
            lines=[
                SaleLineInput(
                    product_id=line.product_id,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                )
                for line in payload.lines
            ],
        )
    )
    return SaleRecordOut.build(result.sale, result.movements)


@router.get("/{sale_id}", response_model=SaleOut)
async def get_sale(
    sale_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*(SALES_ROLES + (UserRole.AUDITOR,)))),
) -> SaleOut:
    sales_repo = SqlAlchemySalesRepository(session)
    use_case = GetSaleUseCase(sales_repo)
    sale = await use_case.execute(GetSaleInput(sale_id=sale_id))
    return SaleOut.from_domain(sale)


@router.get("", response_model=SaleListOut)
async def list_sales(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    customer_id: str | None = Query(None, min_length=1, max_length=26),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*(SALES_ROLES + (UserRole.AUDITOR,)))),
) -> SaleListOut:
    sales_repo = SqlAlchemySalesRepository(session)
    use_case = ListSalesUseCase(sales_repo)
    result = await use_case.execute(
        ListSalesInput(
            page=page,
            limit=limit,
            customer_id=customer_id,
            date_from=date_from,
            date_to=date_to,
        )
    )
    items = [SaleOut.from_domain(sale) for sale in result.sales]
    meta = SalePageMetaOut(page=result.page, limit=result.limit, total=result.total, pages=result.pages)
    return SaleListOut(items=items, meta=meta)
