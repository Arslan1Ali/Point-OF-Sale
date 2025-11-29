from __future__ import annotations

from dataclasses import dataclass

from app.application.catalog.import_utils import parse_decimal
from app.application.catalog.ports import (
    CategoryRepository,
    ProductImportJobRepository,
    ProductRepository,
)
from app.domain.catalog.entities import Product
from app.domain.catalog.import_job import ProductImportItem, ProductImportJob
from app.domain.common.errors import NotFoundError, ValidationError


@dataclass(slots=True)
class ProcessProductImportJobInput:
    job_id: str


class ProcessProductImportJobUseCase:
    def __init__(
        self,
        job_repo: ProductImportJobRepository,
        product_repo: ProductRepository,
        category_repo: CategoryRepository,
    ) -> None:
        self._job_repo = job_repo
        self._product_repo = product_repo
        self._category_repo = category_repo

    async def execute(self, data: ProcessProductImportJobInput) -> ProductImportJob:
        loaded = await self._job_repo.get_job_with_items(data.job_id)
        if loaded is None:
            raise NotFoundError("Import job not found")

        job, raw_items = loaded
        items = list(raw_items)
        self._prepare_for_processing(job, items)

        for item in items:
            await self._process_item(job, item)

        if job.error_count:
            job.mark_failed()
        else:
            job.mark_completed()

        await self._job_repo.save_job(job, items)
        return job

    def _prepare_for_processing(self, job: ProductImportJob, items: list[ProductImportItem]) -> None:
        job.mark_processing()
        job.processed_rows = 0
        job.error_count = 0
        job.errors = []
        for item in items:
            item.reset()

    async def _process_item(self, job: ProductImportJob, item: ProductImportItem) -> None:
        payload = item.payload or {}
        row_number = item.row_number
        sku = (payload.get("sku") or "").strip()
        name = (payload.get("name") or "").strip()

        try:
            retail = parse_decimal(payload.get("retail_price", ""), row_number, "retail_price", positive=True)
            purchase = parse_decimal(
                payload.get("purchase_price", ""),
                row_number,
                "purchase_price",
                positive_or_zero=True,
            )
        except ValidationError as exc:
            self._fail_item(job, item, str(exc))
            return

        category_id = (payload.get("category_id") or None) or None
        if category_id:
            category = await self._category_repo.get_by_id(category_id)
            if category is None:
                self._fail_item(job, item, f"Row {row_number}: category '{category_id}' not found")
                return

        if not sku:
            self._fail_item(job, item, f"Row {row_number}: SKU required")
            return

        existing = await self._product_repo.get_by_sku(sku)
        if existing is not None:
            self._fail_item(job, item, f"Row {row_number}: SKU '{sku}' already exists")
            return

        try:
            product = Product.create(
                name=name,
                sku=sku,
                price_retail=retail,
                purchase_price=purchase,
                currency=payload.get("currency") or "USD",
                category_id=category_id,
            )
        except ValidationError as exc:
            self._fail_item(job, item, f"Row {row_number}: {exc.message}")
            return

        try:
            await self._product_repo.add(product)
        except Exception as exc:  # pragma: no cover - defensive failure path
            self._fail_item(job, item, f"Row {row_number}: unable to create product ({exc})")
            return
        item.mark_completed()
        job.record_success()

    def _fail_item(self, job: ProductImportJob, item: ProductImportItem, message: str) -> None:
        item.mark_failed(message)
        job.record_failure(message)
