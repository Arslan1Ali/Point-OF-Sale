from __future__ import annotations

from dataclasses import dataclass

from app.application.suppliers.ports import SupplierRepository
from app.domain.common.errors import ValidationError
from app.domain.suppliers import Supplier


@dataclass(slots=True)
class ListSuppliersInput:
    page: int = 1
    limit: int = 20
    search: str | None = None
    active: bool | None = None


@dataclass(slots=True)
class ListSuppliersResult:
    suppliers: list[Supplier]
    total: int
    page: int
    limit: int
    pages: int


class ListSuppliersUseCase:
    def __init__(self, repo: SupplierRepository) -> None:
        self._repo = repo

    async def execute(self, data: ListSuppliersInput) -> ListSuppliersResult:
        if data.page < 1:
            raise ValidationError("page must be >= 1")
        if data.limit < 1 or data.limit > 100:
            raise ValidationError("limit must be between 1 and 100")

        offset = (data.page - 1) * data.limit
        suppliers, total = await self._repo.list_suppliers(
            search=data.search,
            active=data.active,
            offset=offset,
            limit=data.limit,
        )
        pages = (total + data.limit - 1) // data.limit if total > 0 else 0
        return ListSuppliersResult(
            suppliers=list(suppliers),
            total=total,
            page=data.page,
            limit=data.limit,
            pages=pages,
        )
