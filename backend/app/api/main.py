from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.middleware.error_handler import DomainErrorMiddleware
from app.api.routers import (
    auth_router,
    categories_router,
    customers_router,
    employees_router,
    inventory_router,
    products_router,
    purchases_router,
    returns_router,
    sales_router,
    suppliers_router,
    tenants_router,
)
from app.core.logging import configure_logging
from app.core.settings import get_settings

configure_logging()
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # pragma: no cover - minimal hook
    # Place future startup/shutdown logic here (e.g., warm caches, close resources)
    yield

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.add_middleware(DomainErrorMiddleware)

if settings.ALLOWED_HOSTS:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )


@app.get("/health")
async def health() -> dict[str, str]:  # pragma: no cover - trivial
    return {"status": "ok"}


app.include_router(products_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(inventory_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(categories_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(sales_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(customers_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(returns_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(suppliers_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(purchases_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(employees_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(tenants_router.router, prefix=settings.API_V1_PREFIX)
