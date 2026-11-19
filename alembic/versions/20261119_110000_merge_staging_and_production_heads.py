"""merge staging schema-reconciliation head with production head

Staging's 20261019_120000 (reconcile known schema drift) and production's
20261102_120000 chain both branched from 20261017_120000. This joins the two
heads so `alembic upgrade head` has a single target. No schema changes.

Revision ID: 20261119_110000
Revises: 20261019_120000, 20261119_100000
Create Date: 2026-11-19
"""

revision = "20261119_110000"
down_revision = ("20261019_120000", "20261119_100000")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
