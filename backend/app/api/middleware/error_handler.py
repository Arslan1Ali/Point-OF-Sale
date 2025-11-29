from __future__ import annotations

import structlog
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from app.core.logging import bind_trace_id, reset_context
from app.domain.common.errors import DomainError

logger = structlog.get_logger(__name__)


class DomainErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        trace_id = bind_trace_id()
        request.state.trace_id = trace_id
        try:
            response = await call_next(request)
        except HTTPException:
            reset_context()
            raise
        except DomainError as exc:
            logger.warning(
                "domain_error",
                trace_id=trace_id,
                error_code=exc.error_code,
                message=exc.message,
                status_code=exc.status_code,
            )
            reset_context()
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.message, "code": exc.error_code, "trace_id": trace_id},
                headers={"X-Trace-Id": trace_id},
            )
        except Exception:  # pragma: no cover - log unexpected
            logger.exception("unhandled_exception", trace_id=trace_id, path=request.url.path)
            reset_context()
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "trace_id": trace_id},
                headers={"X-Trace-Id": trace_id},
            )
        response.headers.setdefault("X-Trace-Id", trace_id)
        reset_context()
        return response
