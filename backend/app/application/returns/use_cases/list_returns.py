from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.application.returns.ports import ReturnsRepository
from app.domain.common.errors import ValidationError
from app.domain.returns import Return


@dataclass(slots=True)
class ListReturnsInput:
    page: int = 1
    limit: int = 20
    sale_id: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


@dataclass(slots=True)
class ListReturnsResult:
    returns: list[Return]
    total: int
    page: int
    limit: int
    pages: int


class ListReturnsUseCase:
    def __init__(self, returns_repo: ReturnsRepository) -> None:
        self._returns_repo = returns_repo

    async def execute(self, data: ListReturnsInput) -> ListReturnsResult:
        if data.page < 1:
            raise ValidationError("page must be >= 1")
        if data.limit < 1 or data.limit > 100:
            raise ValidationError("limit must be between 1 and 100")
        if data.date_from is not None and data.date_to is not None and data.date_from > data.date_to:
            raise ValidationError("date_from must be before or equal to date_to")

        offset = (data.page - 1) * data.limit
        returns, total = await self._returns_repo.list_returns(
            sale_id=data.sale_id,
            date_from=data.date_from,
            date_to=data.date_to,
            offset=offset,
            limit=data.limit,
        )
        pages = (total + data.limit - 1) // data.limit if total > 0 else 0
        return ListReturnsResult(returns=list(returns), total=total, page=data.page, limit=data.limit, pages=pages)
