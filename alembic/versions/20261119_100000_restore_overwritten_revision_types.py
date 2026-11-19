"""restore revision types overwritten with SHOP by the revisor screen

The revisor screen sent the oldest revision's type (migrated revisions are "SHOP")
when saving the newest one, so revisions requested in Odyssey as CAD/Client/Sales/
Template were stored as SHOP. Requesting a revision also saves the chosen type on
the FAB's sales_cts row at the same moment, so where that row hasn't been touched
since, its type is the one the requester picked. Migrated revisions are left alone.

Revision ID: 20261119_100000
Revises: 20261111_100000
"""
from alembic import op


revision = "20261119_100000"
down_revision = "20261111_100000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE revisions r
        SET revision_type = s.revision_type
        FROM sales_cts s
        WHERE s.fab_id = r.fab_id
          AND upper(r.revision_type) = 'SHOP'
          AND r.requested_by NOT IN (SELECT id FROM users WHERE username = 'migration_bot')
          AND lower(coalesce(s.revision_type, '')) IN ('cad', 'client', 'sales', 'template')
          AND abs(extract(epoch FROM (s.updated_at - r.created_at))) < 60
        """
    )


def downgrade() -> None:
    pass
