"""backfill created_at with default

Revision ID: 0014_population_admin_action_logs_column
Revises: 0013_create_admin_action_logs
Create Date: 2025-10-18
"""
from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0014_population_admin_action_logs_column"
down_revision: str | None = "0013_create_admin_action_logs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE admin_action_logs SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP)"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("UPDATE admin_action_logs SET created_at = NULL"))
