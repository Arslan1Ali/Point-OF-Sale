from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.auth.admin_action_log import AdminActionLog
from app.infrastructure.db.models.auth.admin_action_log_model import AdminActionLogModel
from app.shared.pagination import PageParams


class AdminActionLogRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, log: AdminActionLog) -> None:
        model = AdminActionLogModel(
            id=log.id,
            actor_user_id=log.actor_user_id,
            target_user_id=log.target_user_id,
            action=log.action,
            details=log.details,
            trace_id=log.trace_id,
            created_at=log.created_at,
        )
        self._session.add(model)
        await self._session.flush()

    async def search(
        self,
        *,
        actor_user_id: str | None,
        target_user_id: str | None,
        action: str | None,
        start: datetime | None,
        end: datetime | None,
        params: PageParams,
    ) -> tuple[list[AdminActionLog], int]:
        stmt = select(AdminActionLogModel)
        count_stmt: Select[Any] = select(func.count(AdminActionLogModel.id))
        conditions = []
        if actor_user_id:
            conditions.append(AdminActionLogModel.actor_user_id == actor_user_id)
        if target_user_id:
            conditions.append(AdminActionLogModel.target_user_id == target_user_id)
        if action:
            conditions.append(AdminActionLogModel.action == action)
        if start:
            conditions.append(AdminActionLogModel.created_at >= start)
        if end:
            conditions.append(AdminActionLogModel.created_at <= end)

        if conditions:
            stmt = stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)

        stmt = stmt.order_by(AdminActionLogModel.created_at.desc()).offset(params.offset).limit(params.limit)

        rows = await self._session.execute(stmt)
        models = rows.scalars().all()
        items = [self._to_domain(model) for model in models]

        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()
        return items, total

    @staticmethod
    def _to_domain(model: AdminActionLogModel) -> AdminActionLog:
        return AdminActionLog(
            id=model.id,
            actor_user_id=model.actor_user_id,
            target_user_id=model.target_user_id,
            action=model.action,
            details=model.details or {},
            trace_id=model.trace_id,
            created_at=model.created_at,
        )
