from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import RETURNS_ROLES, require_roles
from app.api.schemas.returns import (
    ReturnCreate,
    ReturnListOut,
    ReturnOut,
    ReturnPageMetaOut,
    ReturnRecordOut,
    ReturnSummaryOut,
)
from app.application.returns.use_cases.get_return import GetReturnInput, GetReturnUseCase
from app.application.returns.use_cases.list_returns import ListReturnsInput, ListReturnsUseCase
from app.application.returns.use_cases.record_return import (
    RecordReturnInput,
    RecordReturnUseCase,
    ReturnLineInput,
)
from app.domain.auth.entities import User
from app.infrastructure.db.repositories.inventory_movement_repository import (
    SqlAlchemyInventoryMovementRepository,
)
from app.infrastructure.db.repositories.returns_repository import SqlAlchemyReturnsRepository
from app.infrastructure.db.repositories.sales_repository import SqlAlchemySalesRepository
from app.infrastructure.db.session import get_session

router = APIRouter(prefix="/returns", tags=["returns"])


@router.get("", response_model=ReturnListOut)
async def list_returns(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sale_id: str | None = Query(None, min_length=1, max_length=26),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*RETURNS_ROLES)),
) -> ReturnListOut:
    returns_repo = SqlAlchemyReturnsRepository(session)
    use_case = ListReturnsUseCase(returns_repo)
    result = await use_case.execute(
        ListReturnsInput(
            page=page,
            limit=limit,
            sale_id=sale_id,
            date_from=date_from,
            date_to=date_to,
        )
    )
    items = [ReturnSummaryOut.from_domain(return_) for return_ in result.returns]
    meta = ReturnPageMetaOut(page=result.page, limit=result.limit, total=result.total, pages=result.pages)
    return ReturnListOut(items=items, meta=meta)


@router.post("", response_model=ReturnRecordOut, status_code=status.HTTP_201_CREATED)
async def record_return(
    payload: ReturnCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*RETURNS_ROLES)),
) -> ReturnRecordOut:
    sales_repo = SqlAlchemySalesRepository(session)
    returns_repo = SqlAlchemyReturnsRepository(session)
    inventory_repo = SqlAlchemyInventoryMovementRepository(session)
    use_case = RecordReturnUseCase(sales_repo, returns_repo, inventory_repo)
    result = await use_case.execute(
        RecordReturnInput(
            sale_id=payload.sale_id,
            lines=[
                ReturnLineInput(
                    sale_item_id=line.sale_item_id,
                    quantity=line.quantity,
                )
                for line in payload.lines
            ],
        )
    )
    return ReturnRecordOut.build(result.return_, result.movements)


@router.get("/{return_id}", response_model=ReturnOut)
async def get_return(
    return_id: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_roles(*RETURNS_ROLES)),
) -> ReturnOut:
    returns_repo = SqlAlchemyReturnsRepository(session)
    use_case = GetReturnUseCase(returns_repo)
    return_ = await use_case.execute(GetReturnInput(return_id=return_id))
    return ReturnOut.from_domain(return_)
