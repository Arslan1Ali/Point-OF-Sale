from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0006_create_inventory_movements_table"
down_revision = "0005_create_product_import_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_movements",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("product_id", sa.String(length=26), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(length=8), nullable=False),
        sa.Column("reason", sa.String(length=128), nullable=False),
        sa.Column("reference", sa.String(length=128), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_inventory_movements_product_id", "inventory_movements", ["product_id"])
    op.create_index("ix_inventory_movements_direction", "inventory_movements", ["direction"])
    op.create_index("ix_inventory_movements_reference", "inventory_movements", ["reference"])
    op.create_index("ix_inventory_movements_occurred", "inventory_movements", ["occurred_at"])


def downgrade() -> None:
    op.drop_index("ix_inventory_movements_occurred", table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_reference", table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_direction", table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_product_id", table_name="inventory_movements")
    op.drop_table("inventory_movements")
