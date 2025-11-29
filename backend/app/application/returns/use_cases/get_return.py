from __future__ import annotations

from dataclasses import dataclass

from app.application.returns.ports import ReturnsRepository
from app.domain.common.errors import NotFoundError
from app.domain.returns import Return


@dataclass(slots=True)
class GetReturnInput:
    return_id: str


class GetReturnUseCase:
    def __init__(self, returns_repo: ReturnsRepository) -> None:
        self._returns_repo = returns_repo

    async def execute(self, data: GetReturnInput) -> Return:
        return_ = await self._returns_repo.get_by_id(data.return_id)
        if return_ is None:
            raise NotFoundError(f"Return {data.return_id} not found")
        return return_
