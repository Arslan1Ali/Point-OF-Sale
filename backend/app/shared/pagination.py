from __future__ import annotations

from math import ceil
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PageMeta(BaseModel):
    page: int
    limit: int
    total: int
    pages: int


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    meta: PageMeta

    @staticmethod
    def build(items: list[T], total: int, params: PageParams) -> Page[T]:
        pages = ceil(total / params.limit) if total else 1
        return Page(items=items, meta=PageMeta(page=params.page, limit=params.limit, total=total, pages=pages))
