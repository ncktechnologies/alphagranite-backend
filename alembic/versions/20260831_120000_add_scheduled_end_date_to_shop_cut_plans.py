"""add scheduled_end_date to shop_cut_plans

Revision ID: 20260831_120000
Revises: 20260826_add_miter
Create Date: 2026-08-31 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260831_120000"
down_revision: Union[str, Sequence[str], None] = "20260826_add_miter"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("shop_cut_plans", sa.Column("scheduled_end_date", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("shop_cut_plans", "scheduled_end_date")
