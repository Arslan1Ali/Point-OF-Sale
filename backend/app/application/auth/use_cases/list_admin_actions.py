from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.application.auth.ports import AdminActionLogRepositoryPort
from app.domain.common.errors import ValidationError
from app.shared.pagination import Page, PageParams


@dataclass(slots=True)
class ListAdminActionsInput:
    params: PageParams
    actor_user_id: str | None = None
    target_user_id: str | None = None
    action: str | None = None
    start: datetime | None = None
    end: datetime | None = None


class ListAdminActionsUseCase:
    def __init__(self, logs: AdminActionLogRepositoryPort):
        self._logs = logs

    async def execute(self, data: ListAdminActionsInput) -> Page:
        if data.start and data.end and data.start > data.end:
            raise ValidationError("start date must be before end date", code="invalid_date_range")

        items, total = await self._logs.search(
            actor_user_id=data.actor_user_id,
            target_user_id=data.target_user_id,
            action=data.action,
            start=data.start,
            end=data.end,
            params=data.params,
        )
        return Page.build(items, total, data.params)
