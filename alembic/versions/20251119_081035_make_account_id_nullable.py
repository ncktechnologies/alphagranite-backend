"""make_account_id_nullable

Revision ID: 20251119_081035
Revises: 20251119_073538
Create Date: 2025-11-19 16:10:35

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251119_081035'
down_revision: Union[str, Sequence[str], None] = '20251119_073538'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make account_id column nullable in jobs table."""
    
    # Make account_id nullable
    op.alter_column('jobs', 'account_id',
                    existing_type=sa.Integer(),
                    nullable=True)


def downgrade() -> None:
    """Revert account_id to NOT NULL."""
    
    # Make account_id NOT NULL again
    op.alter_column('jobs', 'account_id',
                    existing_type=sa.Integer(),
                    nullable=False)
