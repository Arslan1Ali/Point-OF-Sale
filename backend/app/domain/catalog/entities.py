from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from app.domain.common.errors import ValidationError
from app.domain.common.identifiers import new_ulid
from app.domain.common.money import Money


@dataclass(slots=True)
class Category:
    id: str
    name: str
    slug: str
    description: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: int = 0

    @staticmethod
    def create(name: str, description: str | None = None) -> Category:
        if not name or not name.strip():
            raise ValidationError("Category name required", code="category.invalid_name")
        normalized_name = name.strip()
        desc = description.strip() if description and description.strip() else None
        return Category(
            id=new_ulid(),
            name=normalized_name,
            slug=Category._slugify(normalized_name),
            description=desc,
        )

    def rename(self, new_name: str) -> None:
        if not new_name or not new_name.strip():
            raise ValidationError("Category name required", code="category.invalid_name")
        normalized = new_name.strip()
        self.name = normalized
        self.slug = self._slugify(normalized)
        self._touch()

    def update_description(self, description: str | None) -> None:
        self.description = description.strip() if description and description.strip() else None
        self._touch()

    @staticmethod
    def _slugify(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or new_ulid().lower()

    def _touch(self) -> None:
        self.version += 1
        self.updated_at = datetime.now(UTC)


@dataclass(slots=True)
class Product:
    id: str
    name: str
    sku: str
    price_retail: Money
    purchase_price: Money
    category_id: str | None = None
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: int = 0

    @staticmethod
    def create(
        name: str,
        sku: str,
        price_retail: Decimal,
        purchase_price: Decimal,
        currency: str = "USD",
        category_id: str | None = None,
    ) -> Product:
        if not name.strip():
            raise ValidationError("Product name required", code="product.invalid_name")
        if not sku.strip():
            raise ValidationError("SKU required", code="product.invalid_sku")
        if purchase_price > price_retail:
            # In retail typical; allow but could warn; enforce here for early safeguard
            raise ValidationError(
                "Purchase price cannot exceed retail price at creation",
                code="product.invalid_purchase_price",
            )
        return Product(
            id=new_ulid(),
            name=name.strip(),
            sku=sku.strip(),
            price_retail=Money(price_retail, currency),
            purchase_price=Money(purchase_price, currency),
            category_id=category_id,
        )

    def rename(self, new_name: str) -> None:
        if not new_name.strip():
            raise ValidationError("Product name required", code="product.invalid_name")
        self.name = new_name.strip()
        self._touch()

    def change_price(self, new_price: Decimal) -> None:
        if new_price <= 0:
            raise ValidationError("Price must be positive", code="product.invalid_retail_price")
        if new_price < self.purchase_price.amount:
            raise ValidationError(
                "Retail price must be >= purchase price",
                code="product.invalid_retail_price",
            )
        self.price_retail = Money(new_price, self.price_retail.currency)
        self._touch()

    def update_purchase_price(self, new_purchase_price: Decimal) -> None:
        if new_purchase_price < 0:
            raise ValidationError("Purchase price cannot be negative", code="product.invalid_purchase_price")
        if new_purchase_price > self.price_retail.amount:
            raise ValidationError(
                "Purchase price cannot exceed retail price",
                code="product.invalid_purchase_price",
            )
        self.purchase_price = Money(new_purchase_price, self.purchase_price.currency)
        self._touch()

    def assign_category(self, category_id: str | None) -> None:
        self.category_id = category_id
        self._touch()

    def deactivate(self) -> bool:
        if not self.active:
            return False
        self.active = False
        self._touch()
        return True

    def _touch(self) -> None:
        self.version += 1
        self.updated_at = datetime.now(UTC)
