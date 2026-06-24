"""add revision_reason to revisions

Revision ID: 20260624_120000
Revises: 20260622_120000
Create Date: 2026-06-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260624_120000"
down_revision: Union[str, Sequence[str], None] = "20260622_120000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("revisions", sa.Column("revision_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("revisions", "revision_reason")
