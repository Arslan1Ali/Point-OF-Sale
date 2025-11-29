from __future__ import annotations

from dataclasses import dataclass

from app.application.catalog.ports import CategoryRepository
from app.domain.catalog.entities import Category
from app.domain.common.errors import ConflictError, ValidationError


@dataclass(slots=True)
class CreateCategoryInput:
    name: str
    description: str | None = None


class CreateCategoryUseCase:
    def __init__(self, repo: CategoryRepository):
        self._repo = repo

    async def execute(self, data: CreateCategoryInput) -> Category:
        category = Category.create(name=data.name, description=data.description)

        existing = await self._repo.get_by_slug(category.slug)
        if existing is not None:
            raise ConflictError("Category with similar name already exists")

        await self._repo.add(category)
        return category
