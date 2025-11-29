from __future__ import annotations

from collections import defaultdict
from typing import Awaitable, Callable, Sequence, TypeVar

from app.application.common.event_dispatcher import EventDispatcher
from app.domain.common.events import DomainEvent

E = TypeVar("E", bound=DomainEvent)
Handler = Callable[[DomainEvent], Awaitable[None]]


class InMemoryEventDispatcher(EventDispatcher):
    """Simple synchronous in-process dispatcher for domain events."""

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[Handler]] = defaultdict(list)

    async def publish(self, event: DomainEvent) -> None:
        for handler in self._collect_handlers(type(event)):
            await handler(event)

    async def publish_many(self, events: Sequence[DomainEvent]) -> None:
        for event in events:
            await self.publish(event)

    def subscribe(self, event_type: type[E], handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    def _collect_handlers(self, event_type: type[DomainEvent]) -> list[Handler]:
        handlers: list[Handler] = []
        for cls in event_type.__mro__:
            if issubclass(cls, DomainEvent):
                handlers.extend(self._handlers.get(cls, []))
        return handlers
