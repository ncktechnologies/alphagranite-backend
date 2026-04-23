"""merge all heads after installer rate

Revision ID: 2026042302
Revises: 20260325_120000, 20260422_090000, 561270688422, 2026042301
Create Date: 2026-04-23
"""

from typing import Sequence, Union


revision: str = "2026042302"
down_revision: Union[str, Sequence[str], None] = (
    "20260325_120000",
    "20260422_090000",
    "561270688422",
    "2026042301",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
