"""add sqft_completed to slabsmith and final programming session notes

Revision ID: 20260811_120000
Revises: 20260806_173000
Create Date: 2026-08-11 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260811_120000"
down_revision: Union[str, Sequence[str], None] = "20260806_173000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("slab_smith_session_notes", sa.Column("sqft_completed", sa.Float(), nullable=True))
    op.add_column("final_programming_session_notes", sa.Column("sqft_completed", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("final_programming_session_notes", "sqft_completed")
    op.drop_column("slab_smith_session_notes", "sqft_completed")
