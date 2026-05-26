"""add extra crew installers to install schedulings

Revision ID: 20260522_120000
Revises: 2026042302
Create Date: 2026-05-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260522_120000"
down_revision: Union[str, Sequence[str], None] = "2026042302"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("install_schedulings", sa.Column("extra_crew_1_id", sa.Integer(), nullable=True))
    op.add_column("install_schedulings", sa.Column("extra_crew_2_id", sa.Integer(), nullable=True))
    op.add_column("install_schedulings", sa.Column("extra_crew_3_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("install_schedulings", "extra_crew_3_id")
    op.drop_column("install_schedulings", "extra_crew_2_id")
    op.drop_column("install_schedulings", "extra_crew_1_id")
