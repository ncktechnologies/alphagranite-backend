"""Add department management

Revision ID: 940e119eecc6
Revises: 164aa7b4d44f
Create Date: 2025-10-21 05:02:58.779116

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '940e119eecc6'
down_revision: Union[str, Sequence[str], None] = '164aa7b4d44f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add department foreign key."""
    # Create foreign key constraint for User.department to reference Department.id
    op.create_foreign_key(
        'fk_user_department', 
        'users', 
        'departments', 
        ['department'], 
        ['id']
    )


def downgrade() -> None:
    """Downgrade schema to remove department foreign key."""
    op.drop_constraint('fk_user_department', 'users', type_='foreignkey')
