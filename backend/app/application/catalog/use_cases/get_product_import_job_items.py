from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.application.catalog.ports import ProductImportJobRepository
from app.domain.catalog.import_job import ImportStatus, ProductImportItem, ProductImportJob
from app.domain.common.errors import NotFoundError
from app.shared.pagination import MAX_PAGE_SIZE, PageParams


@dataclass(slots=True)
class GetProductImportJobItemsInput:
    job_id: str
    page: int = 1
    limit: int = MAX_PAGE_SIZE
    status: ImportStatus | None = None


@dataclass(slots=True)
class GetProductImportJobItemsOutput:
    job: ProductImportJob
    items: Sequence[ProductImportItem]
    total: int
    page: int
    limit: int
    pages: int


class GetProductImportJobItemsUseCase:
    def __init__(self, repo: ProductImportJobRepository) -> None:
        self._repo = repo

    async def execute(self, data: GetProductImportJobItemsInput) -> GetProductImportJobItemsOutput:
        job = await self._repo.get_job(data.job_id)
        if job is None:
            raise NotFoundError("Import job not found")

        params = PageParams(page=data.page, limit=data.limit)
        items, total = await self._repo.list_job_items(
            data.job_id,
            status=data.status,
            offset=params.offset,
            limit=params.limit,
        )
        pages = (total + params.limit - 1) // params.limit if total else 1
        return GetProductImportJobItemsOutput(
            job=job,
            items=items,
            total=total,
            page=params.page,
            limit=params.limit,
            pages=pages,
        )
