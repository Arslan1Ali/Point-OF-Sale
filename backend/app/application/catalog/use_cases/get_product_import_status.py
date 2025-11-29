from __future__ import annotations

from dataclasses import dataclass

from app.application.catalog.ports import ProductImportJobRepository
from app.domain.catalog.import_job import ImportStatus, ProductImportJob


@dataclass(slots=True)
class ProductImportStatusSummary:
    total_jobs: int
    pending: int
    queued: int
    processing: int
    completed: int
    failed: int
    errors: int
    recent_jobs: list[ProductImportJob]


class GetProductImportStatusUseCase:
    def __init__(self, repo: ProductImportJobRepository, *, default_limit: int = 5):
        if default_limit < 0:
            raise ValueError("default_limit must be non-negative")
        self._repo = repo
        self._default_limit = default_limit

    async def execute(self, *, limit: int | None = None) -> ProductImportStatusSummary:
        max_items = self._default_limit if limit is None else max(limit, 0)
        jobs, _total = await self._repo.list_jobs(limit=None)

        counts: dict[ImportStatus, int] = {status: 0 for status in ImportStatus}
        errors = 0
        for job in jobs:
            counts[job.status] += 1
            errors += job.error_count

        return ProductImportStatusSummary(
            total_jobs=len(jobs),
            pending=counts[ImportStatus.PENDING],
            queued=counts[ImportStatus.QUEUED],
            processing=counts[ImportStatus.PROCESSING],
            completed=counts[ImportStatus.COMPLETED],
            failed=counts[ImportStatus.FAILED],
            errors=errors,
            recent_jobs=list(jobs[:max_items] if max_items else []),
        )
