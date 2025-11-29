from __future__ import annotations

import pytest

from app.application.auth.use_cases.record_admin_action import (
    RecordAdminActionInput,
    RecordAdminActionUseCase,
)


class InMemoryAdminLogRepo:
    def __init__(self) -> None:
        self.entries = []

    async def add(self, log):
        self.entries.append(log)


@pytest.mark.asyncio
async def test_record_admin_action_persists_log_with_defaults():
    repo = InMemoryAdminLogRepo()
    use_case = RecordAdminActionUseCase(repo)

    result = await use_case.execute(
        RecordAdminActionInput(
            actor_user_id="actor-1",
            target_user_id="target-1",
            action="user.deactivate",
        )
    )

    assert result.actor_user_id == "actor-1"
    assert result.target_user_id == "target-1"
    assert result.action == "user.deactivate"
    assert result.details == {}
    assert repo.entries and repo.entries[0].id == result.id


@pytest.mark.asyncio
async def test_record_admin_action_includes_details_and_trace():
    repo = InMemoryAdminLogRepo()
    use_case = RecordAdminActionUseCase(repo)

    payload = {"expected_version": 3}
    result = await use_case.execute(
        RecordAdminActionInput(
            actor_user_id="actor-2",
            target_user_id=None,
            action="user.reset_password",
            details=payload,
            trace_id="trace-123",
        )
    )

    assert result.details == {"expected_version": 3}
    assert result.details is not payload
    assert result.trace_id == "trace-123"
    assert repo.entries[0].details == result.details
