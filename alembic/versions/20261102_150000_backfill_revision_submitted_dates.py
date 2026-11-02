"""backfill revisions.actual_end_date for completed revisions

Completing a revision now stamps actual_end_date (the "revision submitted" date
SCT uses). Older completed revisions get their last update time, which is when
they were completed.

Revision ID: 20261102_150000
Revises: 20261102_140000
"""
from alembic import op


revision = "20261102_150000"
down_revision = "20261102_140000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE revisions
        SET actual_end_date = COALESCE(updated_at, created_at)
        WHERE is_completed IS TRUE AND actual_end_date IS NULL
        """
    )


def downgrade() -> None:
    pass
