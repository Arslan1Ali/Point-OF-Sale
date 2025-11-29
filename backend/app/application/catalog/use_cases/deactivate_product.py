from __future__ import annotations

from dataclasses import dataclass

from app.application.catalog.ports import ProductRepository
from app.domain.catalog.entities import Product
from app.domain.common.errors import ConflictError, NotFoundError, ValidationError


@dataclass(slots=True)
class DeactivateProductInput:
    product_id: str
    expected_version: int


class DeactivateProductUseCase:
    def __init__(self, repo: ProductRepository):
        self._repo = repo

    async def execute(self, data: DeactivateProductInput) -> Product:
        product = await self._repo.get_by_id(data.product_id)
        if product is None:
            raise NotFoundError("Product not found")
        if product.version != data.expected_version:
            raise ConflictError("Product was modified by another transaction")

        changed = product.deactivate()
        if not changed:
            raise ValidationError("Product already inactive")

        success = await self._repo.update(product, expected_version=data.expected_version)
        if not success:
            raise ConflictError("Product was modified by another transaction")
        return product
