from __future__ import annotations

from dataclasses import dataclass

from app.application.catalog.ports import ProductImportJobRepository
from app.domain.catalog.import_job import ProductImportJob
from app.domain.common.errors import NotFoundError


@dataclass(slots=True)
class GetProductImportJobInput:
    job_id: str


class GetProductImportJobUseCase:
    def __init__(self, repo: ProductImportJobRepository):
        self._repo = repo

    async def execute(self, data: GetProductImportJobInput) -> ProductImportJob:
        job = await self._repo.get_job(data.job_id)
        if job is None:
            raise NotFoundError("Import job not found")
        return job
