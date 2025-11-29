from __future__ import annotations

import pytest

from app.application.catalog.use_cases.list_categories import (
    ListCategoriesInput,
    ListCategoriesUseCase,
)
from app.domain.catalog.entities import Category


class InMemoryCategoryRepository:
    def __init__(self, categories: list[Category]):
        self._categories = categories

    async def search(
        self,
        *,
        search: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Category], int]:
        items = self._categories
        if search:
            lowered = search.lower()
            items = [
                category
                for category in items
                if lowered in category.name.lower() or lowered in category.slug.lower()
            ]
        total = len(items)
        sliced = items[offset : offset + limit]
        return list(sliced), total


def _make_category(name: str) -> Category:
    return Category.create(name=name)


@pytest.mark.asyncio
async def test_execute_returns_paginated_result():
    categories = [_make_category("Alpha"), _make_category("Beta"), _make_category("Gamma")]
    repo = InMemoryCategoryRepository(categories)
    use_case = ListCategoriesUseCase(repo)

    result = await use_case.execute(ListCategoriesInput(page=1, limit=2))

    assert result.total == 3
    assert result.pages == 2
    assert result.page == 1
    assert result.limit == 2
    assert [category.name for category in result.categories] == ["Alpha", "Beta"]


@pytest.mark.asyncio
async def test_execute_applies_search_filter():
    categories = [_make_category("Coffee"), _make_category("Tea"), _make_category("Snacks")]
    repo = InMemoryCategoryRepository(categories)
    use_case = ListCategoriesUseCase(repo)

    result = await use_case.execute(ListCategoriesInput(page=1, limit=5, search="tea"))

    assert result.total == 1
    assert result.pages == 1
    assert [category.name for category in result.categories] == ["Tea"]
