from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.application.catalog.ports import ProductRepository
from app.domain.catalog.entities import Product
from app.domain.common.errors import ConflictError, NotFoundError, ValidationError


@dataclass(slots=True)
class UpdateProductInput:
    product_id: str
    expected_version: int
    name: str | None = None
    retail_price: Decimal | None = None
    purchase_price: Decimal | None = None
    category_id: str | None = None
    category_id_provided: bool = False


class UpdateProductUseCase:
    def __init__(self, repo: ProductRepository):
        self._repo = repo

    async def execute(self, data: UpdateProductInput) -> Product:
        product = await self._repo.get_by_id(data.product_id)
        if product is None:
            raise NotFoundError("Product not found")
        if product.version != data.expected_version:
            raise ConflictError("Product was modified by another transaction")

        changed = False
        if data.name is not None:
            new_name = data.name.strip()
            if new_name != product.name:
                product.rename(new_name)
                changed = True
        if data.retail_price is not None and data.retail_price != product.price_retail.amount:
            product.change_price(data.retail_price)
            changed = True
        if data.purchase_price is not None and data.purchase_price != product.purchase_price.amount:
            product.update_purchase_price(data.purchase_price)
            changed = True
        if data.category_id_provided:
            new_category = data.category_id
            if new_category != product.category_id:
                product.assign_category(new_category)
                changed = True

        if not changed:
            raise ValidationError("No changes detected")

        success = await self._repo.update(product, expected_version=data.expected_version)
        if not success:
            raise ConflictError("Product was modified by another transaction")
        return product
