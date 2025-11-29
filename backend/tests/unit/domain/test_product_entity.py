from decimal import Decimal

import pytest

from app.domain.catalog.entities import Product
from app.domain.common.errors import ValidationError


def test_create_product_success():
    p = Product.create("Sample", "SKU1", Decimal("10.00"), Decimal("5.00"))
    assert p.name == "Sample"
    assert p.sku == "SKU1"
    assert p.price_retail.amount == Decimal("10.00")
    assert p.purchase_price.amount == Decimal("5.00")
    assert p.version == 0


def test_create_product_purchase_gt_retail_fail():
    with pytest.raises(ValidationError) as exc:
        Product.create("Sample", "SKU2", Decimal("5.00"), Decimal("6.00"))
    assert exc.value.error_code == "product.invalid_purchase_price"
