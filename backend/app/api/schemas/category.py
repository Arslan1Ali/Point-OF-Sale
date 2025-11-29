from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=512)


class CategoryOut(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = dict(from_attributes=True)


class CategoryListMetaOut(BaseModel):
    page: int
    limit: int
    total: int
    pages: int


class CategoryListOut(BaseModel):
    items: list[CategoryOut]
    meta: CategoryListMetaOut
