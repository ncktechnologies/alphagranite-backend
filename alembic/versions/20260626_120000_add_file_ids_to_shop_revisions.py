"""add file_ids to shop_revisions

Revision ID: 20260626_120000
Revises: 20260624_120000
Create Date: 2026-06-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260626_120000"
down_revision: Union[str, Sequence[str], None] = "20260624_120000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("shop_revisions", sa.Column("file_ids", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("shop_revisions", "file_ids")
