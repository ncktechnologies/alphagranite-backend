"""add is_confirmed to install_completions

Revision ID: 20260903_120000
Revises: 20260901_120000
Create Date: 2026-09-03

"""
from alembic import op
import sqlalchemy as sa


revision = "20260903_120000"
down_revision = "20260901_120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "install_completions",
        sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("install_completions", "is_confirmed")