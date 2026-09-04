"""add workstation attendance_required

Revision ID: 20260904_120000
Revises: 20260903_140000
Create Date: 2026-09-04

"""
from alembic import op
import sqlalchemy as sa


revision = "20260904_120000"
down_revision = "20260903_140000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "work_stations",
        sa.Column(
            "attendance_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("work_stations", "attendance_required")