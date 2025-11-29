from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.application.auth.use_cases.list_admin_actions import ListAdminActionsInput, ListAdminActionsUseCase
from app.domain.auth.admin_action_log import AdminActionLog
from app.domain.common.errors import ValidationError
from app.shared.pagination import PageParams


class FakeAdminLogRepo:
    def __init__(self, items: list[AdminActionLog], total: int) -> None:
        self._items = items
        self._total = total

    async def search(self, **kwargs):  # type: ignore[no-untyped-def]
        return self._items, self._total


@pytest.mark.asyncio
async def test_list_admin_actions_returns_page():
    log = AdminActionLog.create(
        actor_user_id="admin",
        target_user_id="user",
        action="user.deactivate",
        details={"expected_version": 1},
    )
    repo = FakeAdminLogRepo([log], 5)
    use_case = ListAdminActionsUseCase(repo)  # type: ignore[arg-type]

    params = PageParams(page=2, limit=1)
    result = await use_case.execute(ListAdminActionsInput(params=params))

    assert result.meta.page == 2
    assert result.meta.total == 5
    assert result.items == [log]


@pytest.mark.asyncio
async def test_list_admin_actions_validates_date_range():
    repo = FakeAdminLogRepo([], 0)
    use_case = ListAdminActionsUseCase(repo)  # type: ignore[arg-type]
    params = PageParams()

    with pytest.raises(ValidationError):
        await use_case.execute(
            ListAdminActionsInput(
                params=params,
                start=datetime(2025, 1, 2, tzinfo=UTC),
                end=datetime(2025, 1, 1, tzinfo=UTC),
            )
        )
