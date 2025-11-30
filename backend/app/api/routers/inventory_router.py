from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import INVENTORY_ROLES, require_roles
from app.api.dependencies.cache import get_cache_service
from app.application.common.cache import CacheService
from app.api.schemas.inventory import InventoryMovementCreate, InventoryMovementRecordOut
from app.application.inventory.use_cases.record_inventory_movement import (
    RecordInventoryMovementInput,
    RecordInventoryMovementUseCase,
)
from app.domain.auth.entities import User
from app.infrastructure.db.repositories.inventory_movement_repository import (
    SqlAlchemyInventoryMovementRepository,
)
from app.infrastructure.db.repositories.inventory_repository import SqlAlchemyProductRepository
from app.infrastructure.db.session import get_session

router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.post("/products/{product_id}/movements", response_model=InventoryMovementRecordOut, status_code=status.HTTP_201_CREATED)
async def record_movement(
    product_id: str,
    payload: InventoryMovementCreate,
    session: AsyncSession = Depends(get_session),
    cache: CacheService = Depends(get_cache_service),
    _: User = Depends(require_roles(*INVENTORY_ROLES)),
) -> InventoryMovementRecordOut:
    product_repo = SqlAlchemyProductRepository(session)
    inventory_repo = SqlAlchemyInventoryMovementRepository(session)
    use_case = RecordInventoryMovementUseCase(product_repo, inventory_repo)
    
    result = await use_case.execute(
        RecordInventoryMovementInput(
            product_id=product_id,
            quantity=payload.quantity,
            direction=payload.direction,
            reason=payload.reason,
            reference=payload.reference,
            occurred_at=payload.occurred_at,
        )
    )
    await cache.clear_prefix("products:list")
    return InventoryMovementRecordOut(
        movement=result.movement,
        stock=result.stock_level
    )
