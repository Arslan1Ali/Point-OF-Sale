from __future__ import annotations

from decimal import Decimal

from app.domain.common.errors import ValidationError


def parse_decimal(
    raw_value: str,
    row_number: int,
    field_name: str,
    *,
    positive: bool = False,
    positive_or_zero: bool = False,
) -> Decimal:
    if not raw_value:
        raise ValidationError(f"Row {row_number}: {field_name} required")
    try:
        value = Decimal(raw_value)
    except Exception as exc:  # pragma: no cover - Decimal error message varies
        raise ValidationError(f"Row {row_number}: {field_name} must be a number") from exc
    if positive and value <= 0:
        raise ValidationError(f"Row {row_number}: {field_name} must be greater than zero")
    if positive_or_zero and value < 0:
        raise ValidationError(f"Row {row_number}: {field_name} cannot be negative")
    return value
