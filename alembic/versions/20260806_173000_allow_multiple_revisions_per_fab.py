"""allow multiple revisions per fab

Revision ID: 20260806_173000
Revises: 20260804_130000
Create Date: 2026-08-06 17:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260806_173000"
down_revision: Union[str, Sequence[str], None] = "20260804_130000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove one-revision-per-fab enforcement.
    op.execute("ALTER TABLE revisions DROP CONSTRAINT IF EXISTS revisions_fab_id_key")
    op.execute("DROP INDEX IF EXISTS revisions_fab_id_key")
    op.execute("CREATE INDEX IF NOT EXISTS ix_revisions_fab_id ON revisions (fab_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_revisions_fab_id")
    op.execute("ALTER TABLE revisions ADD CONSTRAINT revisions_fab_id_key UNIQUE (fab_id)")
