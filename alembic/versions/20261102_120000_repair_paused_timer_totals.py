"""repair total_time_spent on paused drafting/CNC sessions

Pausing used to add the whole running total again on every pause, so paused
sessions show inflated time. Completed sessions were recomputed on end and are
unaffected. A paused session's true total is pause start - session start - pauses.

Revision ID: 20261102_120000
Revises: 20261017_120000
"""
from alembic import op


revision = "20261102_120000"
down_revision = "20261017_120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("drafting_sessions", "cnc_drafting_sessions"):
        op.execute(
            f"""
            UPDATE {table}
            SET total_time_spent = GREATEST(
                CAST(EXTRACT(EPOCH FROM (current_pause_start_time - session_start_time)) AS INTEGER)
                    - COALESCE(total_pause_duration, 0),
                0
            )
            WHERE status IN ('paused', 'on_hold')
              AND current_pause_start_time IS NOT NULL
              AND session_start_time IS NOT NULL
            """
        )


def downgrade() -> None:
    # Data repair only; the inflated values are not worth restoring.
    pass
