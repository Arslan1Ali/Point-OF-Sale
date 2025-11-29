from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0003_create_refresh_tokens_table"
down_revision = "0002_create_users_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS refresh_tokens")
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(length=36), primary_key=True),  # jti (uuid)
        sa.Column("user_id", sa.String(length=26), nullable=False, index=True),
    sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false(), index=True),
        sa.Column("replaced_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("refresh_tokens")