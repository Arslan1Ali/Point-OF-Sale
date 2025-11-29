from __future__ import annotations

from dataclasses import dataclass

from app.domain.common.events import DomainEvent


@dataclass(slots=True, frozen=True)
class SaleRecordedEvent(DomainEvent):
    """Event raised after a sale has been recorded."""

    total_amount: str
    currency: str
    customer_id: str | None
