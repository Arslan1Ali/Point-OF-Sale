"""create admin action logs

Revision ID: 0013_create_admin_action_logs
Revises: 0012_seed_admin_user
Create Date: 2025-10-18
"""
from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0013_create_admin_action_logs"
down_revision: str | None = "0012_seed_admin_user"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "admin_action_logs",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column(
            "actor_user_id",
            sa.String(length=26),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_user_id",
            sa.String(length=26),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_admin_action_logs_actor_user_id",
        "admin_action_logs",
        ["actor_user_id"],
    )
    op.create_index(
        "ix_admin_action_logs_action",
        "admin_action_logs",
        ["action"],
    )
    op.create_index(
        "ix_admin_action_logs_created_at",
        "admin_action_logs",
        ["created_at"],
    )
    op.create_index(
        "ix_admin_action_logs_actor_target",
        "admin_action_logs",
        ["actor_user_id", "target_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_admin_action_logs_actor_target", table_name="admin_action_logs")
    op.drop_index("ix_admin_action_logs_created_at", table_name="admin_action_logs")
    op.drop_index("ix_admin_action_logs_action", table_name="admin_action_logs")
    op.drop_index("ix_admin_action_logs_actor_user_id", table_name="admin_action_logs")
    op.drop_table("admin_action_logs")
