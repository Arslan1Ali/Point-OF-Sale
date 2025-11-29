from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.common.identifiers import new_ulid


@dataclass(slots=True, frozen=True, kw_only=True)
class DomainEvent:
    """Base type for published domain events."""

    aggregate_id: str
    event_id: str = field(default_factory=new_ulid)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_name(self) -> str:
        return self.__class__.__name__


class EventRecorderMixin:
    """Helper mixin for aggregates that capture domain events."""

    __slots__ = ("_pending_events",)

    def __init__(self) -> None:
        self._pending_events: list[DomainEvent] = []

    def record_event(self, event: DomainEvent) -> None:
        self._pending_events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events = self._pending_events[:]
        self._pending_events.clear()
        return events
