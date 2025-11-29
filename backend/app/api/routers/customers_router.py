from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import SALES_ROLES, require_roles
from app.api.schemas.customer import (
    CustomerCreate,
    CustomerDeactivate,
    CustomerDetailOut,
    CustomerListOut,
    CustomerOut,
    CustomerPageMetaOut,
    CustomerSaleOut,
    CustomerSalesListOut,
    CustomerSummaryOut,
    CustomerUpdate,
)
from app.application.customers.use_cases.deactivate_customer import (
    DeactivateCustomerInput,
    DeactivateCustomerUseCase,
)
from app.application.customers.use_cases.get_customer import GetCustomerInput, GetCustomerUseCase
from app.application.customers.use_cases.get_customer_summary import GetCustomerSummaryUseCase
from app.application.customers.use_cases.list_customers import (
    ListCustomersInput,
    ListCustomersUseCase,
)
from app.application.customers.use_cases.register_customer import (
    RegisterCustomerInput,
    RegisterCustomerUseCase,
)
from app.application.customers.use_cases.update_customer import (
    UpdateCustomerInput,
    UpdateCustomerUseCase,
)
from app.application.sales.use_cases.list_customer_sales import (
    ListCustomerSalesInput,
    ListCustomerSalesUseCase,
)
from app.domain.auth.entities import User, UserRole
from app.domain.common.errors import ValidationError
from app.infrastructure.db.repositories.customer_repository import SqlAlchemyCustomerRepository
from app.infrastructure.db.repositories.sales_repository import SqlAlchemySalesRepository
from app.infrastructure.db.session import get_session

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerDetailOut, status_code=status.HTTP_201_CREATED)
async def register_customer(
    payload: CustomerCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*SALES_ROLES)),
) -> CustomerDetailOut:
    repo = SqlAlchemyCustomerRepository(session)
    use_case = RegisterCustomerUseCase(repo)
    customer = await use_case.execute(
        RegisterCustomerInput(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            phone=payload.phone,
        )
    )
    return CustomerDetailOut.from_domain(customer)


@router.get("/{customer_id}", response_model=CustomerDetailOut)
async def get_customer(
    customer_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*(SALES_ROLES + (UserRole.AUDITOR,)))),
) -> CustomerDetailOut:
    repo = SqlAlchemyCustomerRepository(session)
    use_case = GetCustomerUseCase(repo)
    customer = await use_case.execute(GetCustomerInput(customer_id=customer_id))
    return CustomerDetailOut.from_domain(customer)


@router.patch("/{customer_id}", response_model=CustomerDetailOut)
async def update_customer(
    customer_id: str,
    payload: CustomerUpdate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*SALES_ROLES)),
) -> CustomerDetailOut:
    provided = payload.model_fields_set
    update_fields = provided - {"expected_version"}
    if not update_fields:
        raise ValidationError("No update fields provided")

    repo = SqlAlchemyCustomerRepository(session)
    use_case = UpdateCustomerUseCase(repo)
    customer = await use_case.execute(
        UpdateCustomerInput(
            customer_id=customer_id,
            expected_version=payload.expected_version,
            first_name=payload.first_name if "first_name" in provided else None,
            last_name=payload.last_name if "last_name" in provided else None,
            email=payload.email if "email" in provided else None,
            phone=payload.phone if "phone" in provided else None,
            first_name_provided="first_name" in provided,
            last_name_provided="last_name" in provided,
            email_provided="email" in provided,
            phone_provided="phone" in provided,
        )
    )
    return CustomerDetailOut.from_domain(customer)


@router.get("", response_model=CustomerListOut)
async def list_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, min_length=1),
    active: bool | None = Query(None),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*(SALES_ROLES + (UserRole.AUDITOR,)))),
) -> CustomerListOut:
    repo = SqlAlchemyCustomerRepository(session)
    use_case = ListCustomersUseCase(repo)
    result = await use_case.execute(
        ListCustomersInput(
            page=page,
            limit=limit,
            search=search,
            active=active,
        )
    )
    items = [CustomerOut.from_domain(customer) for customer in result.customers]
    meta = CustomerPageMetaOut(
        page=result.page,
        limit=result.limit,
        total=result.total,
        pages=result.pages,
    )
    return CustomerListOut(items=items, meta=meta)


@router.post("/{customer_id}/deactivate", response_model=CustomerDetailOut)
async def deactivate_customer(
    customer_id: str,
    payload: CustomerDeactivate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*SALES_ROLES)),
) -> CustomerDetailOut:
    repo = SqlAlchemyCustomerRepository(session)
    use_case = DeactivateCustomerUseCase(repo)
    customer = await use_case.execute(
        DeactivateCustomerInput(customer_id=customer_id, expected_version=payload.expected_version)
    )
    return CustomerDetailOut.from_domain(customer)


@router.get("/{customer_id}/sales", response_model=CustomerSalesListOut)
async def list_customer_sales(
    customer_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*(SALES_ROLES + (UserRole.AUDITOR,)))),
) -> CustomerSalesListOut:
    customer_repo = SqlAlchemyCustomerRepository(session)
    sales_repo = SqlAlchemySalesRepository(session)
    use_case = ListCustomerSalesUseCase(sales_repo, customer_repo)
    result = await use_case.execute(
        ListCustomerSalesInput(customer_id=customer_id, page=page, limit=limit)
    )
    items = [CustomerSaleOut.from_domain(sale) for sale in result.sales]
    meta = CustomerPageMetaOut(page=result.page, limit=result.limit, total=result.total, pages=result.pages)
    return CustomerSalesListOut(items=items, meta=meta)


@router.get("/{customer_id}/summary", response_model=CustomerSummaryOut)
async def get_customer_summary(
    customer_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*(SALES_ROLES + (UserRole.AUDITOR,)))),
) -> CustomerSummaryOut:
    customer_repo = SqlAlchemyCustomerRepository(session)
    sales_repo = SqlAlchemySalesRepository(session)
    use_case = GetCustomerSummaryUseCase(customer_repo, sales_repo)
    result = await use_case.execute(customer_id)
    return CustomerSummaryOut.from_result(result)
