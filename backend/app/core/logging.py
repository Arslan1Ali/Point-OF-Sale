from __future__ import annotations

import logging
import sys
from typing import Any
from uuid import uuid4

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars


def configure_logging() -> None:  # pragma: no cover (side-effect)
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


def bind_trace_id(trace_id: str | None = None) -> str:
    """Bind a trace ID into the structlog context, generating one if needed."""
    value = trace_id or str(uuid4())
    bind_contextvars(trace_id=value)
    return value


def reset_context() -> None:
    """Clear any request-scoped context variables."""
    clear_contextvars()
