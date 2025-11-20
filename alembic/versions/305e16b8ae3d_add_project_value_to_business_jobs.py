"""add_project_value_to_business_jobs

Revision ID: 305e16b8ae3d
Revises: add_templating_fields
Create Date: 2025-11-19 10:07:01.091890

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '305e16b8ae3d'
down_revision: Union[str, Sequence[str], None] = 'add_templating_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add project_value column to jobs table
    op.add_column('jobs', sa.Column('project_value', sa.Numeric(precision=15, scale=2), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove project_value column from jobs table
    op.drop_column('jobs', 'project_value')
