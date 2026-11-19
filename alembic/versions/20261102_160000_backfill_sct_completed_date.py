"""backfill fabs.sct_completed_date from SCT approvals in the audit trail

The SCT approve endpoint set sct_completed but never sct_completed_date, so
approved FABs showed no SCT Completed date. Use each FAB's latest successful
approve request recorded in audit_trails.

Revision ID: 20261102_160000
Revises: 20261102_150000
"""
from alembic import op


revision = "20261102_160000"
down_revision = "20261102_150000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE fabs
        SET sct_completed_date = approvals.approved_at
        FROM (
            SELECT CAST(substring(request_path FROM '/sales-ct/([0-9]+)/approve$') AS INTEGER) AS fab_id,
                   MAX(created_at) AS approved_at
            FROM audit_trails
            WHERE request_path ~ '/sales-ct/[0-9]+/approve$'
              AND response_status_code BETWEEN 200 AND 299
            GROUP BY 1
        ) AS approvals
        WHERE fabs.id = approvals.fab_id
          AND fabs.sct_completed IS TRUE
          AND fabs.sct_completed_date IS NULL
        """
    )


def downgrade() -> None:
    pass
