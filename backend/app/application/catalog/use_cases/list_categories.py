from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from app.application.catalog.ports import CategoryRepository
from app.domain.catalog.entities import Category
from app.shared.pagination import PageParams


@dataclass(slots=True)
class ListCategoriesInput:
    page: int = 1
    limit: int = 20
    search: str | None = None


@dataclass(slots=True)
class ListCategoriesResult:
    categories: list[Category]
    total: int
    page: int
    limit: int
    pages: int


class ListCategoriesUseCase:
    def __init__(self, repo: CategoryRepository):
        self._repo = repo

    async def execute(self, data: ListCategoriesInput) -> ListCategoriesResult:
        params = PageParams(page=data.page, limit=data.limit)
        categories, total = await self._repo.search(
            search=data.search,
            offset=params.offset,
            limit=params.limit,
        )
        pages = ceil(total / params.limit) if total else 1
        return ListCategoriesResult(
            categories=list(categories),
            total=total,
            page=params.page,
            limit=params.limit,
            pages=pages,
        )
