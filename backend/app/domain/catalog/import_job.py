from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from app.domain.common.errors import ValidationError
from app.domain.common.identifiers import new_ulid


class ImportStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(slots=True)
class ProductImportJob:
    id: str
    original_filename: str
    status: ImportStatus
    total_rows: int
    processed_rows: int
    error_count: int
    errors: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @staticmethod
    def create(original_filename: str, *, total_rows: int) -> ProductImportJob:
        if not original_filename:
            raise ValidationError("Filename required", code="import_job.invalid_filename")
        if total_rows <= 0:
            raise ValidationError("Import file must contain at least one row", code="import_job.empty_file")
        return ProductImportJob(
            id=new_ulid(),
            original_filename=original_filename,
            status=ImportStatus.PENDING,
            total_rows=total_rows,
            processed_rows=0,
            error_count=0,
        )

    def mark_queued(self) -> None:
        self.status = ImportStatus.QUEUED
        self._touch()

    def mark_processing(self) -> None:
        self.status = ImportStatus.PROCESSING
        self._touch()

    def record_success(self) -> None:
        self.processed_rows += 1
        self._touch()

    def record_failure(self, message: str) -> None:
        self.processed_rows += 1
        self.error_count += 1
        if message:
            self.errors.append(message)
        self._touch()

    def mark_completed(self) -> None:
        self.status = ImportStatus.COMPLETED
        self._touch()

    def mark_failed(self) -> None:
        self.status = ImportStatus.FAILED
        self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now(UTC)


@dataclass(slots=True)
class ProductImportItem:
    id: str
    job_id: str
    row_number: int
    payload: dict[str, Any]
    status: ImportStatus
    error_message: str | None = None

    @staticmethod
    def create(job_id: str, row_number: int, payload: dict[str, Any]) -> ProductImportItem:
        if row_number < 1:
            raise ValidationError("Row numbers start at 1", code="import_job.invalid_row_number")
        return ProductImportItem(
            id=new_ulid(),
            job_id=job_id,
            row_number=row_number,
            payload=payload,
            status=ImportStatus.PENDING,
        )

    def mark_failed(self, message: str) -> None:
        self.status = ImportStatus.FAILED
        self.error_message = message

    def mark_completed(self) -> None:
        self.status = ImportStatus.COMPLETED
        self.error_message = None

    def reset(self) -> None:
        self.status = ImportStatus.PENDING
        self.error_message = None
