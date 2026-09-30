"""add is_migrated / migration_source to fabs

Marks FABs that were imported from a legacy system (Caspio) by the data
migration, as opposed to FABs created in Odyssey.

Revision ID: 20260930_120000
Revises: 20260925_120000
Create Date: 2026-09-30

"""
from alembic import op
import sqlalchemy as sa


revision = "20260930_120000"
down_revision = "20260925_120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "fabs",
        sa.Column("is_migrated", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("fabs", sa.Column("migration_source", sa.String(length=50), nullable=True))
    op.create_index("ix_fabs_is_migrated", "fabs", ["is_migrated"])


def downgrade() -> None:
    op.drop_index("ix_fabs_is_migrated", table_name="fabs")
    op.drop_column("fabs", "migration_source")
    op.drop_column("fabs", "is_migrated")
