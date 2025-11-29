from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.domain.common.errors import ValidationError


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        object.__setattr__(self, "amount", self._quantize(self.amount))
        if self.amount < Decimal("0"):
            raise ValidationError("Money amount cannot be negative", code="money.negative_amount")

    @staticmethod
    def _quantize(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def add(self, other: Money) -> Money:
        self._assert_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def subtract(self, other: Money) -> Money:
        self._assert_currency(other)
        if other.amount > self.amount:
            raise ValidationError("Resulting money would be negative", code="money.negative_result")
        return Money(self.amount - other.amount, self.currency)

    def multiply(self, multiplier: int | Decimal) -> Money:
        return Money(self.amount * Decimal(multiplier), self.currency)

    def _assert_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValidationError("Currency mismatch", code="money.currency_mismatch")

    def __lt__(self, other: Money) -> bool:
        self._assert_currency(other)
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        self._assert_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: Money) -> bool:
        self._assert_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        self._assert_currency(other)
        return self.amount >= other.amount

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.currency} {self.amount}"
