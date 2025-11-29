from __future__ import annotations

from typing import Protocol, Sequence

from app.domain.customers import Customer


class CustomerRepository(Protocol):
    async def add(self, customer: Customer) -> None: ...  # pragma: no cover

    async def get_by_email(self, email: str) -> Customer | None: ...  # pragma: no cover

    async def get_by_id(self, customer_id: str) -> Customer | None: ...  # pragma: no cover

    async def update(self, customer: Customer, *, expected_version: int) -> bool: ...  # pragma: no cover

    async def list_customers(
        self,
        *,
        search: str | None = None,
        active: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Customer], int]: ...  # pragma: no cover
