from __future__ import annotations

from typing import Protocol, Sequence

from app.domain.suppliers import Supplier


class SupplierRepository(Protocol):
    async def add(self, supplier: Supplier) -> None: ...  # pragma: no cover

    async def get_by_id(self, supplier_id: str) -> Supplier | None: ...  # pragma: no cover

    async def get_by_email(self, email: str) -> Supplier | None: ...  # pragma: no cover

    async def list_suppliers(
        self,
        *,
        search: str | None = None,
        active: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Supplier], int]: ...  # pragma: no cover
