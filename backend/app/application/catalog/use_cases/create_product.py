from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.application.catalog.ports import ProductRepository
from app.domain.catalog.entities import Product
from app.domain.common.errors import ConflictError


@dataclass(slots=True)
class CreateProductInput:
    name: str
    sku: str
    retail_price: Decimal
    purchase_price: Decimal
    currency: str = "USD"
    category_id: str | None = None


class CreateProductUseCase:
    def __init__(self, repo: ProductRepository):
        self._repo = repo

    async def execute(self, data: CreateProductInput) -> Product:
        existing = await self._repo.get_by_sku(data.sku)
        if existing is not None:
            raise ConflictError("SKU already exists")
        product = Product.create(
            name=data.name,
            sku=data.sku,
            price_retail=data.retail_price,
            purchase_price=data.purchase_price,
            currency=data.currency,
            category_id=data.category_id,
        )
        await self._repo.add(product)
        return product
