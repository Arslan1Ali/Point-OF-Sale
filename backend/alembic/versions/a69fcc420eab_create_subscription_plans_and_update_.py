"""create_subscription_plans_and_update_tenants

Revision ID: a69fcc420eab
Revises: 0016_create_tenants_and_update_users
Create Date: 2025-11-30 20:19:19.051326

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'a69fcc420eab'
down_revision: Union[str, None] = '0016_create_tenants_and_update_users'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create subscription_plans table
    op.create_table('subscription_plans',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('duration_months', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Update tenants table
    # SQLite requires batch mode for alter table
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.add_column(sa.Column('subscription_plan_id', sa.String(length=26), nullable=True))
        batch_op.create_foreign_key('fk_tenants_subscription_plan_id', 'subscription_plans', ['subscription_plan_id'], ['id'])
        batch_op.drop_column('subscription_plan')


def downgrade() -> None:
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.add_column(sa.Column('subscription_plan', sa.VARCHAR(length=50), nullable=True))
        batch_op.drop_constraint('fk_tenants_subscription_plan_id', type_='foreignkey')
        batch_op.drop_column('subscription_plan_id')

    op.drop_table('subscription_plans')
