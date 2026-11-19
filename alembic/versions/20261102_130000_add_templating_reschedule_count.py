"""add reschedule_count to templatings

Revision ID: 20261102_130000
Revises: 20261102_120000
"""
from alembic import op
import sqlalchemy as sa


revision = "20261102_130000"
down_revision = "20261102_120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "templatings",
        sa.Column("reschedule_count", sa.Integer(), nullable=False, server_default="0"),
    )
    # Records already flagged as rescheduled have been rescheduled at least once.
    op.execute("UPDATE templatings SET reschedule_count = 1 WHERE rescheduled IS TRUE")


def downgrade() -> None:
    op.drop_column("templatings", "reschedule_count")
