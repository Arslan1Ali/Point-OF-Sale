from __future__ import annotations

from datetime import datetime
from typing import Mapping, Protocol, Sequence

from app.domain.returns import Return, ReturnItem


class ReturnsRepository(Protocol):
    async def add_return(self, return_: Return, items: Sequence[ReturnItem]) -> None: ...  # pragma: no cover

    async def get_returned_quantities(self, sale_item_ids: Sequence[str]) -> Mapping[str, int]: ...  # pragma: no cover

    async def get_by_id(self, return_id: str) -> Return | None: ...  # pragma: no cover

    async def list_returns(
        self,
        *,
        sale_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Return], int]: ...  # pragma: no cover
