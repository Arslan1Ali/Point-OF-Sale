from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.application.catalog.ports import ProductRepository
from app.domain.catalog.entities import Product
from app.domain.common.errors import ValidationError
from app.shared.pagination import PageParams

VALID_SORT_FIELDS = {"created_at", "name", "sku", "retail_price"}
VALID_SORT_DIRECTIONS = {"asc", "desc"}


@dataclass(slots=True)
class ListProductsInput:
    page: int = 1
    limit: int = 20
    search: str | None = None
    category_id: str | None = None
    active: bool | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    sort_by: str = "created_at"
    sort_direction: str = "desc"


@dataclass(slots=True)
class ListProductsOutput:
    products: list[Product]
    total: int
    page: int
    limit: int
    pages: int


class ListProductsUseCase:
    def __init__(self, repository: ProductRepository):
        self._repository = repository

    async def execute(self, data: ListProductsInput) -> ListProductsOutput:
        params = PageParams(page=data.page, limit=data.limit)

        if data.min_price is not None and data.max_price is not None and data.min_price > data.max_price:
            raise ValidationError("min_price cannot be greater than max_price")

        sort_by = data.sort_by or "created_at"
        sort_direction = data.sort_direction or "desc"
        if sort_by not in VALID_SORT_FIELDS:
            raise ValidationError(f"Invalid sort_by field '{sort_by}'")
        if sort_direction not in VALID_SORT_DIRECTIONS:
            raise ValidationError("sort_direction must be 'asc' or 'desc'")

        products, total = await self._repository.list_products(
            search=data.search,
            category_id=data.category_id,
            active=data.active,
            min_price=data.min_price,
            max_price=data.max_price,
            sort_by=sort_by,
            sort_direction=sort_direction,
            offset=params.offset,
            limit=params.limit,
        )

        pages = max(1, (total + params.limit - 1) // params.limit)
        return ListProductsOutput(
            products=list(products),
            total=total,
            page=params.page,
            limit=params.limit,
            pages=pages,
        )
