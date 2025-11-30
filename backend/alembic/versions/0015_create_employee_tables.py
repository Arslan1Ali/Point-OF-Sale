from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0015_create_employee_tables"
down_revision = "0014_population_admin_action_logs_column"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create employees table
    op.create_table(
        "employees",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("position", sa.String(length=100), nullable=False),
        sa.Column("hire_date", sa.Date(), nullable=False),
        sa.Column("base_salary", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_employees_email", "employees", ["email"], unique=True)
    op.create_index("ix_employees_is_active", "employees", ["is_active"])

    # 2. Create employee_bonuses table
    op.create_table(
        "employee_bonuses",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("employee_id", sa.String(length=26), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("date_awarded", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_employee_bonuses_employee_id", "employee_bonuses", ["employee_id"])

    # 3. Create salary_history table
    op.create_table(
        "salary_history",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("employee_id", sa.String(length=26), nullable=False),
        sa.Column("previous_salary", sa.Numeric(12, 2), nullable=False),
        sa.Column("new_salary", sa.Numeric(12, 2), nullable=False),
        sa.Column("change_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_salary_history_employee_id", "salary_history", ["employee_id"])


def downgrade() -> None:
    op.drop_index("ix_salary_history_employee_id", table_name="salary_history")
    op.drop_table("salary_history")
    
    op.drop_index("ix_employee_bonuses_employee_id", table_name="employee_bonuses")
    op.drop_table("employee_bonuses")
    
    op.drop_index("ix_employees_is_active", table_name="employees")
    op.drop_index("ix_employees_email", table_name="employees")
    op.drop_table("employees")
