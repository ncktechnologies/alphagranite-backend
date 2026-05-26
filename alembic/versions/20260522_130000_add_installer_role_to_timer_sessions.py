"""add installer role to installer timer sessions

Revision ID: 20260522_130000
Revises: 20260522_120000
Create Date: 2026-05-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260522_130000"
down_revision: Union[str, Sequence[str], None] = "20260522_120000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "installer_job_timer_sessions",
        sa.Column("installer_role", sa.String(length=20), nullable=False, server_default="lead"),
    )

    op.execute(
        """
        UPDATE installer_job_timer_sessions ijts
        SET installer_role = 'extra_crew'
        FROM install_schedulings ins
        WHERE ijts.fab_id = ins.fab_id
          AND ijts.installer_id IN (ins.extra_crew_1_id, ins.extra_crew_2_id, ins.extra_crew_3_id)
        """
    )


def downgrade() -> None:
    op.drop_column("installer_job_timer_sessions", "installer_role")
