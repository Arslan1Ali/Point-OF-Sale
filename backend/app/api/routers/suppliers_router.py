from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import AUDIT_ROLES, PURCHASING_ROLES, require_roles
from app.api.schemas.suppliers import (
    SupplierCreate,
    SupplierDetailOut,
    SupplierListOut,
    SupplierOut,
    SupplierPageMetaOut,
    SupplierSummaryOut,
)
from app.application.suppliers.use_cases.get_supplier import GetSupplierInput, GetSupplierUseCase
from app.application.suppliers.use_cases.get_supplier_summary import GetSupplierSummaryUseCase
from app.application.suppliers.use_cases.list_suppliers import (
    ListSuppliersInput,
    ListSuppliersUseCase,
)
from app.application.suppliers.use_cases.register_supplier import (
    RegisterSupplierInput,
    RegisterSupplierUseCase,
)
from app.domain.auth.entities import User, UserRole
from app.infrastructure.db.repositories.purchase_repository import SqlAlchemyPurchaseRepository
from app.infrastructure.db.repositories.supplier_repository import SqlAlchemySupplierRepository
from app.infrastructure.db.session import get_session
from app.shared.pagination import PageParams

READ_SUPPLIER_ROLES: tuple[UserRole, ...] = tuple(dict.fromkeys(PURCHASING_ROLES + AUDIT_ROLES))

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.post("", response_model=SupplierOut, status_code=status.HTTP_201_CREATED)
async def register_supplier(
    payload: SupplierCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*PURCHASING_ROLES)),
) -> SupplierOut:
    repo = SqlAlchemySupplierRepository(session)
    use_case = RegisterSupplierUseCase(repo)
    supplier = await use_case.execute(
        RegisterSupplierInput(
            name=payload.name,
            contact_email=payload.contact_email,
            contact_phone=payload.contact_phone,
        )
    )
    return SupplierOut.from_domain(supplier)


@router.get("", response_model=SupplierListOut)
async def list_suppliers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, min_length=1),
    active: bool | None = Query(None),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*READ_SUPPLIER_ROLES)),
) -> SupplierListOut:
    params = PageParams(page=page, limit=limit)
    repo = SqlAlchemySupplierRepository(session)
    use_case = ListSuppliersUseCase(repo)
    result = await use_case.execute(
        ListSuppliersInput(
            page=params.page,
            limit=params.limit,
            search=search,
            active=active,
        )
    )
    items = [SupplierOut.from_domain(supplier) for supplier in result.suppliers]
    meta = SupplierPageMetaOut(
        page=result.page,
        limit=result.limit,
        total=result.total,
        pages=result.pages,
    )
    return SupplierListOut(items=items, meta=meta)


@router.get("/{supplier_id}", response_model=SupplierDetailOut)
async def get_supplier(
    supplier_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*READ_SUPPLIER_ROLES)),
) -> SupplierDetailOut:
    repo = SqlAlchemySupplierRepository(session)
    use_case = GetSupplierUseCase(repo)
    supplier = await use_case.execute(GetSupplierInput(supplier_id=supplier_id))
    return SupplierDetailOut.from_domain(supplier)


@router.get("/{supplier_id}/summary", response_model=SupplierSummaryOut)
async def get_supplier_summary(
    supplier_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*READ_SUPPLIER_ROLES)),
) -> SupplierSummaryOut:
    supplier_repo = SqlAlchemySupplierRepository(session)
    purchase_repo = SqlAlchemyPurchaseRepository(session)
    use_case = GetSupplierSummaryUseCase(supplier_repo, purchase_repo)
    result = await use_case.execute(supplier_id)
    return SupplierSummaryOut.from_result(result)
