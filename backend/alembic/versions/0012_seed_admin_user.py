"""seed admin user

Revision ID: 0012_seed_admin_user
Revises: 0011_create_purchases_tables
Create Date: 2025-10-09
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012_seed_admin_user"
down_revision: str | None = "0011_create_purchases_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ADMIN_ID = "01K74P30H8ZD9XG9PRDG91FHHY"
ADMIN_EMAIL = "admin@retailpos.com"
ADMIN_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$C+Hc2zsn5Lw3RuidUyqlFA$blZWX+Jvy8UIdCh7dzBy6k67gutO2nCo57yCw2YXqGI"
)
ADMIN_PASSWORD = "AdminPass123!"  # noqa: S105

def upgrade() -> None:
    now = datetime.now(timezone.utc).isoformat()
    insert_stmt = sa.text(
        """
        INSERT INTO users (id, email, password_hash, role, active, created_at, updated_at, version)
        SELECT :id, :email, :password_hash, :role, 1, :created_at, :updated_at, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM users WHERE email = :email_check
        )
        """
    )
    conn = op.get_bind()
    conn.execute(
        insert_stmt,
        {
            "id": ADMIN_ID,
            "email": ADMIN_EMAIL,
            "password_hash": ADMIN_PASSWORD_HASH,
            "role": "ADMIN",
            "created_at": now,
            "updated_at": now,
            "email_check": ADMIN_EMAIL,
        },
    )


def downgrade() -> None:
    delete_stmt = sa.text("DELETE FROM users WHERE email = :email")
    conn = op.get_bind()
    conn.execute(delete_stmt, {"email": ADMIN_EMAIL})
