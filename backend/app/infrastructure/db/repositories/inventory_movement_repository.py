from __future__ import annotations

from datetime import UTC, datetime
from typing import Sequence

from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.inventory.ports import InventoryMovementRepository
from app.domain.inventory import InventoryMovement, MovementDirection, StockLevel
from app.infrastructure.db.models.inventory_movement_model import InventoryMovementModel


class SqlAlchemyInventoryMovementRepository(InventoryMovementRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, movement: InventoryMovement) -> None:
        model = InventoryMovementModel(
            id=movement.id,
            product_id=movement.product_id,
            quantity=movement.quantity,
            direction=movement.direction.value,
            reason=movement.reason,
            reference=movement.reference,
            occurred_at=movement.occurred_at,
            created_at=movement.created_at,
        )
        self._session.add(model)
        await self._session.flush()

    async def list_for_product(
        self,
        product_id: str,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[Sequence[InventoryMovement], int]:
        base_filter = InventoryMovementModel.product_id == product_id

        query = (
            select(InventoryMovementModel)
            .where(base_filter)
            .order_by(
                desc(InventoryMovementModel.occurred_at),
                desc(InventoryMovementModel.created_at),
            )
            .offset(offset)
        )
        if limit is not None:
            query = query.limit(limit)

        count_query = select(func.count(InventoryMovementModel.id)).where(base_filter)

        res = await self._session.execute(query)
        rows = res.scalars().all()
        count_res = await self._session.execute(count_query)
        total = count_res.scalar_one()
        movements = [self._to_entity(row) for row in rows]
        return movements, int(total)

    async def get_stock_level(self, product_id: str, *, as_of: datetime | None = None) -> StockLevel:
        delta_case = case(
            (
                InventoryMovementModel.direction == MovementDirection.IN.value,
                InventoryMovementModel.quantity,
            ),
            else_=-InventoryMovementModel.quantity,
        )
        cutoff = _normalize_timestamp(as_of) if as_of is not None else None
        stmt = select(
            func.coalesce(func.sum(delta_case), 0).label("total_delta"),
            func.max(InventoryMovementModel.occurred_at).label("last_occurred"),
        ).where(InventoryMovementModel.product_id == product_id)
        if cutoff is not None:
            stmt = stmt.where(InventoryMovementModel.occurred_at <= cutoff)
        res = await self._session.execute(stmt)
        total_delta, last_occurred = res.one()
        effective_as_of = cutoff or last_occurred or datetime.now(UTC)
        return StockLevel.from_movements(
            product_id,
            total_delta=int(total_delta),
            as_of=effective_as_of,
        )

    async def get_stock_levels(self, product_ids: Sequence[str]) -> dict[str, int]:
        if not product_ids:
            return {}
            
        delta_case = case(
            (
                InventoryMovementModel.direction == MovementDirection.IN.value,
                InventoryMovementModel.quantity,
            ),
            else_=-InventoryMovementModel.quantity,
        )
        
        stmt = (
            select(
                InventoryMovementModel.product_id,
                func.coalesce(func.sum(delta_case), 0).label("total_delta")
            )
            .where(InventoryMovementModel.product_id.in_(product_ids))
            .group_by(InventoryMovementModel.product_id)
        )
        
        res = await self._session.execute(stmt)
        rows = res.all()
        return {row.product_id: int(row.total_delta) for row in rows}

    async def get_last_movement_at(self, product_id: str) -> datetime | None:
        stmt = (
            select(func.max(InventoryMovementModel.occurred_at))
            .where(InventoryMovementModel.product_id == product_id)
        )
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    def _to_entity(self, model: InventoryMovementModel) -> InventoryMovement:
        return InventoryMovement(
            id=model.id,
            product_id=model.product_id,
            quantity=model.quantity,
            direction=MovementDirection(model.direction),
            reason=model.reason,
            reference=model.reference,
            occurred_at=model.occurred_at,
            created_at=model.created_at,
        )


def _normalize_timestamp(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
