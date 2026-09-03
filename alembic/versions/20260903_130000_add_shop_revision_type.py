"""add shop_revision_type to shop_revisions

Revision ID: 20260903_130000
Revises: 20260903_120000
Create Date: 2026-09-03

"""
from alembic import op
import sqlalchemy as sa


revision = "20260903_130000"
down_revision = "20260903_120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "shop_revisions",
        sa.Column("shop_revision_type", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("shop_revisions", "shop_revision_type")