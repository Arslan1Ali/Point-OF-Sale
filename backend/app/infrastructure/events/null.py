from __future__ import annotations

from typing import Sequence

from app.application.common.event_dispatcher import EventDispatcher, EventHandler
from app.domain.common.events import DomainEvent


class NullEventDispatcher(EventDispatcher):
    """No-op dispatcher used when no subscribers are required."""

    async def publish(self, event: DomainEvent) -> None:  # pragma: no cover - intentionally empty
        return None

    async def publish_many(self, events: Sequence[DomainEvent]) -> None:  # pragma: no cover - intentionally empty
        return None

    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:  # pragma: no cover
        return None
