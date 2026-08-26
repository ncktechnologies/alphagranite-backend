"""add saw_miter_lnft and wj_miter_lnft to fabs

Revision ID: 20260826_add_miter
Revises: 20260811_120000
Create Date: 2026-08-26

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260826_add_miter'
down_revision = '20260811_120000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('fabs', sa.Column('saw_miter_lnft', sa.Float(), nullable=True))
    op.add_column('fabs', sa.Column('wj_miter_lnft', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('fabs', 'wj_miter_lnft')
    op.drop_column('fabs', 'saw_miter_lnft')
