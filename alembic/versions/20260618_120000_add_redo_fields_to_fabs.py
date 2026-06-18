"""add redo fields to fabs

Revision ID: 20260618_120000
Revises: 20260608_140000
Create Date: 2026-06-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260618_120000"
down_revision: Union[str, Sequence[str], None] = "20260608_140000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("fabs", sa.Column("redo_total_sqft", sa.Float(), nullable=True))
    op.add_column("fabs", sa.Column("redo_department", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True))
    op.add_column("fabs", sa.Column("cost_per_sqft", sa.Float(), nullable=True))
    op.add_column("fabs", sa.Column("redo_requested_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))


def downgrade() -> None:
    op.drop_column("fabs", "redo_requested_by")
    op.drop_column("fabs", "cost_per_sqft")
    op.drop_column("fabs", "redo_department")
    op.drop_column("fabs", "redo_total_sqft")
