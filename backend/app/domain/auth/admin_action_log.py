from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.domain.common.identifiers import new_ulid


@dataclass(slots=True)
class AdminActionLog:
    id: str
    actor_user_id: str
    target_user_id: str | None
    action: str
    details: dict[str, Any]
    trace_id: str | None
    created_at: datetime

    @staticmethod
    def create(
        *,
        actor_user_id: str,
        target_user_id: str | None,
        action: str,
        details: dict[str, Any] | None = None,
        trace_id: str | None = None,
    ) -> AdminActionLog:
        payload: dict[str, Any] = dict(details) if details else {}
        return AdminActionLog(
            id=new_ulid(),
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            action=action,
            details=payload,
            trace_id=trace_id,
            created_at=datetime.now(UTC),
        )
