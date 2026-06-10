"""add revision_feedback to shop_revisions

Revision ID: 20260608_130000
Revises: 20260605_120000
Create Date: 2026-06-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260608_130000"
down_revision: Union[str, Sequence[str], None] = "20260605_120000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("shop_revisions", sa.Column("revision_feedback", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("shop_revisions", "revision_feedback")
