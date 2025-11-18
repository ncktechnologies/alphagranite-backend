"""merge migration heads

Revision ID: a47d77f3fdc1
Revises: 2025_02_16_0000, notes_to_json_array
Create Date: 2025-11-18 19:25:37.938901

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a47d77f3fdc1'
down_revision: Union[str, Sequence[str], None] = ('2025_02_16_0000', 'notes_to_json_array')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
