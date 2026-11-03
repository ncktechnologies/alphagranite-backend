"""add the Completed Work by Department report to Roles & Permissions

The report used the Completion Report permission until now. It gets its own
action menu ('completed_work_report'), and every role that could see it through
Completion Report keeps the same access, so nobody loses the report on deploy.

Revision ID: 20261103_100000
Revises: 20261102_160000
"""
from alembic import op


revision = "20261103_100000"
down_revision = "20261102_160000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO action_menus (name, code, created_at, updated_at)
        SELECT 'Completed Work by Department', 'completed_work_report', NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM action_menus WHERE code = 'completed_work_report')
        """
    )
    op.execute(
        """
        INSERT INTO role_permissions (permission_id, role_id, action_menu_id, created_at, updated_at)
        SELECT rp.permission_id, rp.role_id, new_menu.id, NOW(), NOW()
        FROM role_permissions rp
        JOIN action_menus old_menu ON old_menu.id = rp.action_menu_id AND old_menu.code = 'completion_report'
        CROSS JOIN (SELECT id FROM action_menus WHERE code = 'completed_work_report' ORDER BY id LIMIT 1) AS new_menu
        WHERE NOT EXISTS (
            SELECT 1 FROM role_permissions existing
            WHERE existing.role_id = rp.role_id AND existing.action_menu_id = new_menu.id
        )
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM role_permissions
        WHERE action_menu_id IN (SELECT id FROM action_menus WHERE code = 'completed_work_report')
        """
    )
    op.execute("DELETE FROM action_menus WHERE code = 'completed_work_report'")
