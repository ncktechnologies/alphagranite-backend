"""add cutlist_complete to fabs

Revision ID: add_cutlist_complete_to_fabs
Revises: add_is_completed_stages
Create Date: 2026-03-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_cutlist_complete_to_fabs'
down_revision = 'add_is_completed_stages'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE fabs
        ADD COLUMN IF NOT EXISTS cutlist_complete BOOLEAN NOT NULL DEFAULT FALSE
    """)


def downgrade() -> None:
    op.drop_column('fabs', 'cutlist_complete')
