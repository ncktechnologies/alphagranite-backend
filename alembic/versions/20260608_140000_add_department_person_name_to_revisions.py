"""add department and person_name to revisions

Revision ID: 20260608_140000
Revises: 20260608_130000
Create Date: 2026-06-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260608_140000"
down_revision: Union[str, Sequence[str], None] = "20260608_130000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("revisions", sa.Column("department", sa.String(length=255), nullable=True))
    op.add_column("revisions", sa.Column("person_name", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("revisions", "person_name")
    op.drop_column("revisions", "department")
