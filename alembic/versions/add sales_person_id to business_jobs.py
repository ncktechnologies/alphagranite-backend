"""add sales_person_id to business_jobs"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260112_add_sales_person_id_to_business_jobs"
down_revision = "36b7386d9414"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column(
        "business_jobs",
        sa.Column("sales_person_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "fk_business_jobs_sales_person_id_users",
        "business_jobs",
        "users",
        ["sales_person_id"],
        ["id"],
        ondelete="SET NULL"
    )
    op.create_index(
        "ix_business_jobs_sales_person_id",
        "business_jobs",
        ["sales_person_id"]
    )

def downgrade():
    op.drop_index("ix_business_jobs_sales_person_id", table_name="business_jobs")
    op.drop_constraint("fk_business_jobs_sales_person_id_users", "business_jobs", type_="foreignkey")
    op.drop_column("business_jobs", "sales_person_id")