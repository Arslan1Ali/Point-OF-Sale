from __future__ import annotations

from dataclasses import dataclass

from app.application.catalog.ports import ProductImportJobRepository
from app.domain.catalog.import_job import ImportStatus, ProductImportJob
from app.shared.pagination import MAX_PAGE_SIZE, PageParams


@dataclass(slots=True)
class ListProductImportJobsInput:
    page: int = 1
    limit: int = MAX_PAGE_SIZE
    status: ImportStatus | None = None


@dataclass(slots=True)
class ListProductImportJobsOutput:
    jobs: list[ProductImportJob]
    total: int


class ListProductImportJobsUseCase:
    def __init__(self, repo: ProductImportJobRepository):
        self._repo = repo

    async def execute(self, data: ListProductImportJobsInput) -> ListProductImportJobsOutput:
        params = PageParams(page=data.page, limit=data.limit)
        jobs, total = await self._repo.list_jobs(
            status=data.status,
            offset=params.offset,
            limit=params.limit,
        )

        return ListProductImportJobsOutput(jobs=list(jobs), total=total)
