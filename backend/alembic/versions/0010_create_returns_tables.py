from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0010_create_returns_tables"
down_revision = "0009_add_customer_to_sales"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "returns",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column(
            "sale_id",
            sa.String(length=26),
            sa.ForeignKey("sales.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_quantity", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_returns_sale_id", "returns", ["sale_id"])

    op.create_table(
        "return_items",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column(
            "return_id",
            sa.String(length=26),
            sa.ForeignKey("returns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sale_item_id",
            sa.String(length=26),
            sa.ForeignKey("sale_items.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.String(length=26),
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_return_items_return_id", "return_items", ["return_id"])
    op.create_index("ix_return_items_sale_item_id", "return_items", ["sale_item_id"])


def downgrade() -> None:
    op.drop_index("ix_return_items_sale_item_id", table_name="return_items")
    op.drop_index("ix_return_items_return_id", table_name="return_items")
    op.drop_table("return_items")

    op.drop_index("ix_returns_sale_id", table_name="returns")
    op.drop_table("returns")
