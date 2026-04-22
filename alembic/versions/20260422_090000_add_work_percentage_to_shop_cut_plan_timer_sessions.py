"""add work_percentage to shop_cut_plan_timer_sessions

Revision ID: 20260422_090000
Revises: 20260401_120000
Create Date: 2026-04-22 09:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260422_090000"
down_revision: Union[str, Sequence[str], None] = "20260401_120000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "shop_cut_plan_timer_sessions",
        sa.Column("work_percentage", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("shop_cut_plan_timer_sessions", "work_percentage", server_default=None)


def downgrade() -> None:
    op.drop_column("shop_cut_plan_timer_sessions", "work_percentage")
