from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import AUDIT_ROLES, PURCHASING_ROLES, require_roles
from app.api.schemas.purchases import (
    PurchaseCreate,
    PurchaseListOut,
    PurchaseOut,
    PurchasePageMetaOut,
    PurchaseRecordOut,
)
from app.application.purchases.use_cases.get_purchase import GetPurchaseInput, GetPurchaseUseCase
from app.application.purchases.use_cases.list_purchases import (
    ListPurchasesInput,
    ListPurchasesUseCase,
)
from app.application.purchases.use_cases.record_purchase import (
    PurchaseLineInput,
    RecordPurchaseInput,
    RecordPurchaseUseCase,
)
from app.domain.auth.entities import User, UserRole
from app.infrastructure.db.repositories.inventory_movement_repository import (
    SqlAlchemyInventoryMovementRepository,
)
from app.infrastructure.db.repositories.inventory_repository import SqlAlchemyProductRepository
from app.infrastructure.db.repositories.purchase_repository import SqlAlchemyPurchaseRepository
from app.infrastructure.db.repositories.supplier_repository import SqlAlchemySupplierRepository
from app.infrastructure.db.session import get_session
from app.shared.pagination import PageParams

READ_PURCHASING_ROLES: tuple[UserRole, ...] = tuple(dict.fromkeys(PURCHASING_ROLES + AUDIT_ROLES))

router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.post("", response_model=PurchaseRecordOut, status_code=status.HTTP_201_CREATED)
async def record_purchase(
    payload: PurchaseCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*PURCHASING_ROLES)),
) -> PurchaseRecordOut:
    supplier_repo = SqlAlchemySupplierRepository(session)
    product_repo = SqlAlchemyProductRepository(session)
    purchase_repo = SqlAlchemyPurchaseRepository(session)
    inventory_repo = SqlAlchemyInventoryMovementRepository(session)
    use_case = RecordPurchaseUseCase(supplier_repo, product_repo, purchase_repo, inventory_repo)
    result = await use_case.execute(
        RecordPurchaseInput(
            supplier_id=payload.supplier_id,
            currency=payload.currency,
            lines=[
                PurchaseLineInput(
                    product_id=line.product_id,
                    quantity=line.quantity,
                    unit_cost=line.unit_cost,
                )
                for line in payload.lines
            ],
        )
    )
    return PurchaseRecordOut.build(result.purchase, result.movements)


@router.get("", response_model=PurchaseListOut)
async def list_purchases(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    supplier_id: str | None = Query(None, min_length=1, max_length=26),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*READ_PURCHASING_ROLES)),
) -> PurchaseListOut:
    params = PageParams(page=page, limit=limit)
    purchase_repo = SqlAlchemyPurchaseRepository(session)
    use_case = ListPurchasesUseCase(purchase_repo)
    result = await use_case.execute(
        ListPurchasesInput(
            page=params.page,
            limit=params.limit,
            supplier_id=supplier_id,
        )
    )
    items = [PurchaseOut.from_domain(purchase) for purchase in result.purchases]
    meta = PurchasePageMetaOut(
        page=result.page,
        limit=result.limit,
        total=result.total,
        pages=result.pages,
    )
    return PurchaseListOut(items=items, meta=meta)


@router.get("/{purchase_id}", response_model=PurchaseOut)
async def get_purchase(
    purchase_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*READ_PURCHASING_ROLES)),
) -> PurchaseOut:
    purchase_repo = SqlAlchemyPurchaseRepository(session)
    use_case = GetPurchaseUseCase(purchase_repo)
    purchase = await use_case.execute(GetPurchaseInput(purchase_id=purchase_id))
    return PurchaseOut.from_domain(purchase)
