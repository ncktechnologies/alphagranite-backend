"""Reconcile confirmed schema drift without changing existing application data.

Revision ID: 20261019_120000
Revises: 20261017_120000
"""
from alembic import context, op
import sqlalchemy as sa


revision = "20261019_120000"
down_revision = "20261017_120000"
branch_labels = None
depends_on = None


def _performance_tables():
    metadata = sa.MetaData()
    sa.Table("users", metadata, sa.Column("id", sa.Integer(), primary_key=True))
    return (
        sa.Table(
            "performance_static_data", metadata,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("year", sa.Integer(), nullable=False),
            sa.Column("total_expenses", sa.Float()),
            sa.Column("total_wages", sa.Float()),
            sa.Column("breakeven_gross_revenue", sa.Float()),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime()),
            sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id")),
        ),
        sa.Table(
            "subcontractor_weekly_labor", metadata,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("year", sa.Integer(), nullable=False),
            sa.Column("week_ending", sa.Date(), nullable=False),
            sa.Column("total_labor_cost", sa.Float()),
            sa.Column("head_count", sa.Float()),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime()),
            sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id")),
        ),
    )


def _ensure_columns(table_name, columns):
    existing = {column["name"]: column for column in sa.inspect(op.get_bind()).get_columns(table_name)}
    for column in columns:
        actual = existing.get(column.name)
        if actual is None:
            if column.primary_key or (not column.nullable and column.server_default is None):
                raise RuntimeError(f"Cannot safely reconstruct required column {table_name}.{column.name}")
            op.add_column(table_name, sa.Column(
                column.name, column.type, nullable=column.nullable, server_default=column.server_default,
            ))
            continue
        compatible = isinstance(actual["type"], type(column.type))
        if isinstance(column.type, sa.String):
            compatible = compatible and actual["type"].length == column.type.length
        if isinstance(column.type, sa.DateTime):
            compatible = compatible and actual["type"].timezone == column.type.timezone
        nullable_mismatch = not column.nullable and actual["nullable"] and not column.primary_key
        if not compatible or nullable_mismatch:
            raise RuntimeError(f"Incompatible definition for {table_name}.{column.name}; manual review required")


def _ensure_index(table_name, name, columns, unique=False):
    indexes = sa.inspect(op.get_bind()).get_indexes(table_name)
    existing = next((index for index in indexes if index["name"] == name), None)
    if existing is None:
        op.create_index(name, table_name, columns, unique=unique)
    elif (
        existing["column_names"] != columns
        or bool(existing["unique"]) != unique
        or existing.get("dialect_options", {}).get("postgresql_where") is not None
    ):
        raise RuntimeError(f"Incompatible index {name}; manual review required")


def upgrade() -> None:
    if context.is_offline_mode():
        raise RuntimeError("Schema reconciliation requires an online database connection")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        bind.execute(sa.text("SET LOCAL lock_timeout = '5s'"))
        bind.execute(sa.text("SET LOCAL statement_timeout = '60s'"))

    _ensure_columns("fabs", [
        sa.Column("is_migrated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("migration_source", sa.String(length=50)),
    ])
    _ensure_columns("accounts", [
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    ])
    _ensure_index("fabs", "ix_fabs_is_migrated", ["is_migrated"])
    _ensure_index("accounts", "ix_accounts_is_active", ["is_active"])

    for table in _performance_tables():
        table.create(bind, checkfirst=True)
        _ensure_columns(table.name, table.columns)
        inspector = sa.inspect(bind)
        if inspector.get_pk_constraint(table.name)["constrained_columns"] != ["id"]:
            raise RuntimeError(f"Incompatible primary key on {table.name}; manual review required")
        foreign_keys = inspector.get_foreign_keys(table.name)
        updated_by_keys = [key for key in foreign_keys if "updated_by" in key["constrained_columns"]]
        if not updated_by_keys:
            op.create_foreign_key(
                f"fk_{table.name}_updated_by_users", table.name, "users", ["updated_by"], ["id"],
            )
        elif len(updated_by_keys) != 1 or (
            updated_by_keys[0]["constrained_columns"] != ["updated_by"]
            or updated_by_keys[0]["referred_table"] != "users"
            or updated_by_keys[0]["referred_columns"] != ["id"]
        ):
            raise RuntimeError(f"Incompatible updated_by foreign key on {table.name}; manual review required")

    _ensure_index("performance_static_data", "ix_performance_static_data_year", ["year"], unique=True)
    _ensure_index("subcontractor_weekly_labor", "ix_subcontractor_weekly_labor_year", ["year"])
    _ensure_index(
        "subcontractor_weekly_labor", "ix_subcontractor_weekly_labor_week_ending", ["week_ending"], unique=True,
    )


def downgrade() -> None:
    raise RuntimeError("Reconciliation is irreversible: restored objects may predate this migration")