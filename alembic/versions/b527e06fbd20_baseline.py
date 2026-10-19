"""baseline: schema as of the migration cleanup

The migrations before 20260701_130000 were removed in commit 293c855, and
20260701_130000 was re-pointed at this revision id. This no-op baseline makes
the chain resolvable again; databases stamped at b527e06fbd20 (or any later
revision) upgrade normally. It does not create the schema: a fresh database
must be built from the models/dumps, then stamped.

Revision ID: b527e06fbd20
Revises:
Create Date: 2026-09-22

"""

revision = "b527e06fbd20"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
