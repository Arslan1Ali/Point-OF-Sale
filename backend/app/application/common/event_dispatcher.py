from __future__ import annotations

from typing import Awaitable, Callable, Protocol, Sequence, TypeVar

from app.domain.common.events import DomainEvent

EventHandler = Callable[[DomainEvent], Awaitable[None]]
E = TypeVar("E", bound=DomainEvent)


class EventDispatcher(Protocol):
    """Contract for publishing domain events."""

    async def publish(self, event: DomainEvent) -> None: ...

    async def publish_many(self, events: Sequence[DomainEvent]) -> None: ...

    def subscribe(self, event_type: type[E], handler: EventHandler) -> None: ...
