from decimal import Decimal

import pytest

from app.application.catalog.ports import ProductRepository
from app.application.catalog.use_cases.create_product import (
    CreateProductInput,
    CreateProductUseCase,
)
from app.domain.catalog.entities import Product
from app.domain.common.errors import ConflictError


class InMemoryRepo(ProductRepository):
    def __init__(self):
        self.items: dict[str, Product] = {}

    async def add(self, product: Product) -> None:
        self.items[product.sku] = product

    async def get_by_sku(self, sku: str):
        return self.items.get(sku)


@pytest.mark.asyncio
async def test_create_product_use_case_success():
    repo = InMemoryRepo()
    uc = CreateProductUseCase(repo)
    data = CreateProductInput(
        name="Test",
        sku="SKU1",
        retail_price=Decimal("10.00"),
        purchase_price=Decimal("5.00"),
    )
    product = await uc.execute(data)
    assert product.sku == "SKU1"
    assert product.price_retail.amount == Decimal("10.00")


@pytest.mark.asyncio
async def test_create_product_duplicate_sku():
    repo = InMemoryRepo()
    uc = CreateProductUseCase(repo)
    data = CreateProductInput(
        name="Test",
        sku="SKU1",
        retail_price=Decimal("10.00"),
        purchase_price=Decimal("5.00"),
    )
    await uc.execute(data)
    with pytest.raises(ConflictError):
        await uc.execute(data)
