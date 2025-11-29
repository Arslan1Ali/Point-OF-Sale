from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0008_create_customers_table"
down_revision = "0007_create_sales_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("first_name", sa.String(length=120), nullable=False),
        sa.Column("last_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index("ix_customers_first_name", "customers", ["first_name"])
    op.create_index("ix_customers_last_name", "customers", ["last_name"])
    op.create_index("ix_customers_active", "customers", ["active"])
    op.create_index("ix_customers_created_at", "customers", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_customers_created_at", table_name="customers")
    op.drop_index("ix_customers_active", table_name="customers")
    op.drop_index("ix_customers_last_name", table_name="customers")
    op.drop_index("ix_customers_first_name", table_name="customers")
    op.drop_table("customers")
