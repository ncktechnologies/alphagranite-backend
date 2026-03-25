"""add task_id to files

Revision ID: 20260325_120000
Revises: add_is_completed_stages
Create Date: 2026-03-25 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260325_120000"
down_revision: Union[str, Sequence[str], None] = "add_is_completed_stages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("files", sa.Column("task_id", sa.Integer(), nullable=True))
    op.create_index("ix_files_task_id", "files", ["task_id"], unique=False)
    op.create_foreign_key("fk_files_task_id_shop_cut_plans", "files", "shop_cut_plans", ["task_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_files_task_id_shop_cut_plans", "files", type_="foreignkey")
    op.drop_index("ix_files_task_id", table_name="files")
    op.drop_column("files", "task_id")