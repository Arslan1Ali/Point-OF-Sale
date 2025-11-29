from __future__ import annotations

from dataclasses import dataclass

from app.application.catalog.ports import ImportScheduler, ProductImportJobRepository
from app.domain.catalog.import_job import ImportStatus, ProductImportItem, ProductImportJob
from app.domain.common.errors import NotFoundError, ValidationError


@dataclass(slots=True)
class RetryProductImportJobInput:
    job_id: str


class RetryProductImportJobUseCase:
    def __init__(
        self,
        repo: ProductImportJobRepository,
        scheduler: ImportScheduler,
    ) -> None:
        self._repo = repo
        self._scheduler = scheduler

    async def execute(self, data: RetryProductImportJobInput) -> ProductImportJob:
        loaded = await self._repo.get_job_with_items(data.job_id)
        if loaded is None:
            raise NotFoundError("Import job not found")

        job, raw_items = loaded
        items = list(raw_items)

        if job.status not in {ImportStatus.FAILED}:
            raise ValidationError("Only failed import jobs can be retried")

        self._reset_job(job, items)
        await self._repo.save_job(job, items)
        await self._scheduler.enqueue(job)

        refreshed = await self._repo.get_job(job.id)
        return refreshed or job

    def _reset_job(self, job: ProductImportJob, items: list[ProductImportItem]) -> None:
        job.status = ImportStatus.PENDING
        job.processed_rows = 0
        job.error_count = 0
        job.errors = []
        for item in items:
            item.reset()
        job.mark_queued()
