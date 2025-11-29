from __future__ import annotations

from dataclasses import dataclass

from app.application.sales.ports import SalesRepository
from app.domain.common.errors import NotFoundError
from app.domain.sales import Sale


@dataclass(slots=True)
class GetSaleInput:
    sale_id: str


class GetSaleUseCase:
    def __init__(self, sales_repo: SalesRepository) -> None:
        self._sales_repo = sales_repo

    async def execute(self, data: GetSaleInput) -> Sale:
        sale = await self._sales_repo.get_by_id(data.sale_id)
        if sale is None:
            raise NotFoundError("Sale not found")
        return sale
