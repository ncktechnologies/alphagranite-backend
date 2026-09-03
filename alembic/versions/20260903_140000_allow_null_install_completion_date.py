"""allow null install completion date

Revision ID: 20260903_140000
Revises: 20260903_130000
Create Date: 2026-09-03

"""
from alembic import op
import sqlalchemy as sa


revision = "20260903_140000"
down_revision = "20260903_130000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "install_completions",
        "completion_date",
        existing_type=sa.DateTime(),
        nullable=True,
    )


def downgrade() -> None:
    op.execute(
        "UPDATE install_completions "
        "SET completion_date = install_date "
        "WHERE completion_date IS NULL"
    )
    op.alter_column(
        "install_completions",
        "completion_date",
        existing_type=sa.DateTime(),
        nullable=False,
    )