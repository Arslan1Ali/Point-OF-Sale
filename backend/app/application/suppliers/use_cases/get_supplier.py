from __future__ import annotations

from dataclasses import dataclass

from app.application.suppliers.ports import SupplierRepository
from app.domain.common.errors import NotFoundError
from app.domain.suppliers import Supplier


@dataclass(slots=True)
class GetSupplierInput:
    supplier_id: str


class GetSupplierUseCase:
    def __init__(self, repo: SupplierRepository) -> None:
        self._repo = repo

    async def execute(self, data: GetSupplierInput) -> Supplier:
        supplier = await self._repo.get_by_id(data.supplier_id)
        if supplier is None:
            raise NotFoundError("Supplier not found")
        return supplier
