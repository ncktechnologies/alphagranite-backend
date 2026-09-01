"""add work percentage to stage session notes

Revision ID: 20260901_120000
Revises: 20260831_120000
Create Date: 2026-09-01 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260901_120000"
down_revision: Union[str, Sequence[str], None] = "20260831_120000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("slab_smith_session_notes", sa.Column("work_percentage_done", sa.Float(), nullable=True))
    op.add_column("final_programming_session_notes", sa.Column("work_percentage_done", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("final_programming_session_notes", "work_percentage_done")
    op.drop_column("slab_smith_session_notes", "work_percentage_done")