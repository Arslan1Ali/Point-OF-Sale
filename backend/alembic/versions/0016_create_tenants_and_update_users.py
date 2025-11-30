"""create tenants and update users

Revision ID: 0016
Revises: 0015
Create Date: 2025-11-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0016_create_tenants_and_update_users'
down_revision = '0015_create_employee_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'tenants' not in tables:
        # Create tenants table
        op.create_table('tenants',
            sa.Column('id', sa.String(length=26), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('domain', sa.String(length=255), nullable=True),
            sa.Column('active', sa.Boolean(), nullable=True),
            sa.Column('subscription_plan', sa.String(length=50), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_tenants_domain'), 'tenants', ['domain'], unique=True)
        op.create_index(op.f('ix_tenants_name'), 'tenants', ['name'], unique=True)

    # Add tenant_id to users table using batch mode for SQLite support
    # Check if column exists first to avoid error if partial run
    columns = [c['name'] for c in inspector.get_columns('users')]
    if 'tenant_id' not in columns:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('tenant_id', sa.String(length=26), nullable=True))
            batch_op.create_index(op.f('ix_users_tenant_id'), ['tenant_id'], unique=False)
            batch_op.create_foreign_key('fk_users_tenant_id', 'tenants', ['tenant_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_tenant_id', type_='foreignkey')
        batch_op.drop_index(op.f('ix_users_tenant_id'))
        batch_op.drop_column('tenant_id')

    op.drop_index(op.f('ix_tenants_name'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_domain'), table_name='tenants')
    op.drop_table('tenants')
