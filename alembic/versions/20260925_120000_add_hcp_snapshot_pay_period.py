"""add pay period (week) to hcp payroll and roster snapshots

Each HCP pull covers the Monday-Sunday week before the pull, so snapshots are
stamped with that week to let reports place them into week-ending buckets.

Revision ID: 20260925_120000
Revises: 20260925_090000
Create Date: 2026-09-25 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260925_120000"
down_revision: Union[str, Sequence[str], None] = "20260925_090000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (table, pull timestamp column used to backfill existing rows)
TABLES = (
    ("hcp_payroll_report_snapshots", "created_at"),
    ("hcp_staff_roster_snapshots", "pulled_at"),
)


def upgrade() -> None:
    for table, pulled_col in TABLES:
        op.add_column(table, sa.Column("period_start", sa.Date(), nullable=True))
        op.add_column(table, sa.Column("period_end", sa.Date(), nullable=True))
        op.create_index(op.f(f"ix_{table}_period_end"), table, ["period_end"], unique=False)
        # Last completed Mon-Sun week before the pull: ISODOW (Mon=1..Sun=7) days back lands on the prior Sunday.
        op.execute(
            f"""
            UPDATE {table}
            SET period_end = {pulled_col}::date - EXTRACT(ISODOW FROM {pulled_col})::int,
                period_start = {pulled_col}::date - EXTRACT(ISODOW FROM {pulled_col})::int - 6
            WHERE period_end IS NULL
            """
        )


def downgrade() -> None:
    for table, _ in TABLES:
        op.drop_index(op.f(f"ix_{table}_period_end"), table_name=table)
        op.drop_column(table, "period_end")
        op.drop_column(table, "period_start")
