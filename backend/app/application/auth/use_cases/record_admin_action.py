from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.application.auth.ports import AdminActionLogRepositoryPort
from app.domain.auth.admin_action_log import AdminActionLog


@dataclass(slots=True)
class RecordAdminActionInput:
    actor_user_id: str
    target_user_id: str | None
    action: str
    details: dict[str, Any] | None = None
    trace_id: str | None = None


class RecordAdminActionUseCase:
    def __init__(self, logs: AdminActionLogRepositoryPort):
        self._logs = logs

    async def execute(self, data: RecordAdminActionInput) -> AdminActionLog:
        log = AdminActionLog.create(
            actor_user_id=data.actor_user_id,
            target_user_id=data.target_user_id,
            action=data.action,
            details=data.details,
            trace_id=data.trace_id,
        )
        await self._logs.add(log)
        return log
