from __future__ import annotations

import pytest

from app.domain.catalog.entities import Category
from app.domain.common.errors import ValidationError


def test_create_category_generates_slug_and_trims():
    category = Category.create(name="  Hot Beverages  ", description=" Warm drinks ")
    assert category.name == "Hot Beverages"
    assert category.slug == "hot-beverages"
    assert category.description == "Warm drinks"
    assert category.version == 0


def test_create_category_requires_name():
    with pytest.raises(ValidationError) as exc:
        Category.create(name="   ")
    assert exc.value.error_code == "category.invalid_name"


def test_rename_updates_slug_and_version():
    category = Category.create(name="Beverages")
    previous_version = category.version
    category.rename("Cold Drinks")
    assert category.name == "Cold Drinks"
    assert category.slug == "cold-drinks"
    assert category.version == previous_version + 1


def test_update_description_handles_none_and_trims():
    category = Category.create(name="Snacks", description=" Tasty ")
    category.update_description(" Yum ")
    assert category.description == "Yum"
    category.update_description(None)
    assert category.description is None
