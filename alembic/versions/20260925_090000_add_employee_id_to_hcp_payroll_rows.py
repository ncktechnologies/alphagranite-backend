"""add employee_id to hcp_payroll_report_rows

Revision ID: 20260925_090000
Revises: 20260922_130000
Create Date: 2026-09-25 09:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260925_090000"
down_revision: Union[str, Sequence[str], None] = "20260922_130000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "hcp_payroll_report_rows"


def upgrade() -> None:
    op.add_column(TABLE, sa.Column("employee_id", sa.String(length=100), nullable=True))
    op.create_index(op.f(f"ix_{TABLE}_employee_id"), TABLE, ["employee_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f(f"ix_{TABLE}_employee_id"), table_name=TABLE)
    op.drop_column(TABLE, "employee_id")
