"""add stone_type_id to stone_colors

Revision ID: 20260401_120000
Revises: add_cutlist_complete_to_fabs
Create Date: 2026-04-01 12:00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260401_120000"
down_revision = "add_cutlist_complete_to_fabs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("stone_colors", sa.Column("stone_type_id", sa.Integer(), nullable=True))
    op.create_index("ix_stone_colors_stone_type_id", "stone_colors", ["stone_type_id"], unique=False)
    op.create_foreign_key(
        "fk_stone_colors_stone_type_id_stone_types",
        "stone_colors",
        "stone_types",
        ["stone_type_id"],
        ["id"],
    )

    op.execute(
        """
        DO $$
        DECLARE existing_constraint text;
        BEGIN
            SELECT tc.constraint_name
            INTO existing_constraint
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            WHERE tc.table_name = 'stone_colors'
              AND tc.constraint_type = 'UNIQUE'
              AND kcu.column_name = 'name'
            LIMIT 1;

            IF existing_constraint IS NOT NULL THEN
                EXECUTE format('ALTER TABLE stone_colors DROP CONSTRAINT %I', existing_constraint);
            END IF;
        END $$;
        """
    )

    op.create_unique_constraint(
        "uq_stone_colors_type_name",
        "stone_colors",
        ["stone_type_id", "name"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_stone_colors_type_name", "stone_colors", type_="unique")
    op.create_unique_constraint("stone_colors_name_key", "stone_colors", ["name"])
    op.drop_constraint("fk_stone_colors_stone_type_id_stone_types", "stone_colors", type_="foreignkey")
    op.drop_index("ix_stone_colors_stone_type_id", table_name="stone_colors")
    op.drop_column("stone_colors", "stone_type_id")