from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from app.application.catalog.ports import ProductRepository
from app.application.inventory.ports import InventoryMovementRepository
from app.domain.common.errors import NotFoundError
from app.domain.inventory import InventoryMovement
from app.shared.pagination import PageParams


@dataclass(slots=True)
class ListInventoryMovementsInput:
    product_id: str
    page: int = 1
    limit: int = 20


@dataclass(slots=True)
class ListInventoryMovementsResult:
    product_id: str
    movements: list[InventoryMovement]
    total: int
    page: int
    limit: int
    pages: int


class ListInventoryMovementsUseCase:
    def __init__(self, product_repo: ProductRepository, inventory_repo: InventoryMovementRepository):
        self._product_repo = product_repo
        self._inventory_repo = inventory_repo

    async def execute(self, data: ListInventoryMovementsInput) -> ListInventoryMovementsResult:
        product = await self._product_repo.get_by_id(data.product_id)
        if product is None:
            raise NotFoundError("Product not found")

        params = PageParams(page=data.page, limit=data.limit)
        movements, total = await self._inventory_repo.list_for_product(
            product.id,
            offset=params.offset,
            limit=params.limit,
        )
        pages = ceil(total / params.limit) if total else 1
        return ListInventoryMovementsResult(
            product_id=product.id,
            movements=list(movements),
            total=total,
            page=params.page,
            limit=params.limit,
            pages=pages,
        )
