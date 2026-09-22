"""align hcp config with shared credentials and two fixed settings ids

Revision ID: 20260922_130000
Revises: 20260922_120000
Create Date: 2026-09-22 13:00:00

Corrective: 20260922_120000 was applied in an earlier form that added
`report_kind` and kept a single `report_settings_id`. Written idempotently so it
is safe whether or not that earlier form reached a given database.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260922_130000"
down_revision: Union[str, Sequence[str], None] = "20260922_120000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "hcp_payroll_source_configs"


def upgrade() -> None:
    op.execute(
        f"ALTER TABLE {TABLE} ADD COLUMN IF NOT EXISTS payroll_settings_id "
        "VARCHAR(100) NOT NULL DEFAULT '89798180'"
    )
    op.execute(
        f"ALTER TABLE {TABLE} ADD COLUMN IF NOT EXISTS roster_settings_id "
        "VARCHAR(100) NOT NULL DEFAULT '93428419'"
    )

    # Preserve any previously configured payroll report id.
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = '{TABLE}' AND column_name = 'report_settings_id'
            ) THEN
                UPDATE {TABLE}
                   SET payroll_settings_id = report_settings_id
                 WHERE report_settings_id IS NOT NULL
                   AND report_settings_id <> ''
                   AND report_settings_id <> '93428419';
            END IF;
        END $$;
        """
    )

    op.execute(
        f"CREATE INDEX IF NOT EXISTS ix_{TABLE}_payroll_settings_id ON {TABLE} (payroll_settings_id)"
    )
    op.execute(
        f"CREATE INDEX IF NOT EXISTS ix_{TABLE}_roster_settings_id ON {TABLE} (roster_settings_id)"
    )

    op.execute(f"DROP INDEX IF EXISTS ix_{TABLE}_report_settings_id")
    op.execute(f"DROP INDEX IF EXISTS ix_{TABLE}_report_kind")
    op.execute(f"ALTER TABLE {TABLE} DROP COLUMN IF EXISTS report_settings_id")
    op.execute(f"ALTER TABLE {TABLE} DROP COLUMN IF EXISTS report_kind")


def downgrade() -> None:
    op.execute(
        f"ALTER TABLE {TABLE} ADD COLUMN IF NOT EXISTS report_settings_id "
        "VARCHAR(100) NOT NULL DEFAULT '89798180'"
    )
    op.execute(
        f"ALTER TABLE {TABLE} ADD COLUMN IF NOT EXISTS report_kind "
        "VARCHAR(50) NOT NULL DEFAULT 'labor_cost'"
    )
    op.execute(f"UPDATE {TABLE} SET report_settings_id = payroll_settings_id")
    op.execute(
        f"CREATE INDEX IF NOT EXISTS ix_{TABLE}_report_settings_id ON {TABLE} (report_settings_id)"
    )
    op.execute(f"CREATE INDEX IF NOT EXISTS ix_{TABLE}_report_kind ON {TABLE} (report_kind)")

    op.execute(f"DROP INDEX IF EXISTS ix_{TABLE}_payroll_settings_id")
    op.execute(f"DROP INDEX IF EXISTS ix_{TABLE}_roster_settings_id")
    op.execute(f"ALTER TABLE {TABLE} DROP COLUMN IF EXISTS payroll_settings_id")
    op.execute(f"ALTER TABLE {TABLE} DROP COLUMN IF EXISTS roster_settings_id")
