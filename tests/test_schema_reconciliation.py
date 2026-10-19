import importlib.util
import os
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "alembic/versions/20261019_120000_reconcile_known_schema_drift.py"
)
spec = importlib.util.spec_from_file_location("schema_reconciliation", MIGRATION_PATH)
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)


@pytest.fixture
def connection(monkeypatch):
    url = os.environ.get("SCHEMA_RECONCILIATION_TEST_URL", "sqlite://")
    parsed_url = sa.engine.make_url(url)
    if parsed_url.get_backend_name() != "sqlite" and parsed_url.database != "schema_reconciliation_test":
        raise RuntimeError("Integration tests require the dedicated schema_reconciliation_test database")
    engine = sa.create_engine(url)
    monkeypatch.setattr(migration.context, "is_offline_mode", lambda: False)
    try:
        with engine.connect() as bind:
            transaction = bind.begin()
            try:
                bind.execute(sa.text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
                bind.execute(sa.text("CREATE TABLE fabs (id INTEGER PRIMARY KEY)"))
                bind.execute(sa.text("CREATE TABLE accounts (id INTEGER PRIMARY KEY)"))
                bind.execute(sa.text("INSERT INTO fabs (id) VALUES (1)"))
                bind.execute(sa.text("INSERT INTO accounts (id) VALUES (1)"))
                with Operations.context(MigrationContext.configure(bind)):
                    yield bind
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


def test_reconciliation_repairs_missing_objects_and_defaults(connection):
    migration.upgrade()
    inspector = sa.inspect(connection)
    assert {"performance_static_data", "subcontractor_weekly_labor"}.issubset(inspector.get_table_names())
    assert connection.execute(sa.text("SELECT is_migrated, migration_source FROM fabs")).one() == (0, None)
    assert connection.execute(sa.text("SELECT is_active FROM accounts")).scalar_one() == 1
    assert len(inspector.get_foreign_keys("performance_static_data")) == 1
    assert len(inspector.get_foreign_keys("subcontractor_weekly_labor")) == 1
    assert inspector.get_indexes("performance_static_data")[0]["unique"]


def test_reconciliation_is_repeatable_and_preserves_existing_data(connection):
    migration.upgrade()
    connection.execute(sa.text("UPDATE fabs SET is_migrated = true, migration_source = 'caspio'"))
    connection.execute(sa.text("UPDATE accounts SET is_active = false"))
    connection.execute(sa.text("INSERT INTO performance_static_data (year, total_expenses) VALUES (2026, 123.5)"))
    migration.upgrade()
    assert connection.execute(sa.text("SELECT is_migrated, migration_source FROM fabs")).one() == (1, "caspio")
    assert connection.execute(sa.text("SELECT is_active FROM accounts")).scalar_one() == 0
    assert connection.execute(sa.text("SELECT total_expenses FROM performance_static_data")).scalar_one() == 123.5


def test_reconciliation_repairs_missing_indexes(connection):
    migration.upgrade()
    connection.execute(sa.text("DROP INDEX ix_accounts_is_active"))
    connection.execute(sa.text("DROP INDEX ix_subcontractor_weekly_labor_week_ending"))
    migration.upgrade()
    assert sa.inspect(connection).get_indexes("accounts")[0]["name"] == "ix_accounts_is_active"
    indexes = sa.inspect(connection).get_indexes("subcontractor_weekly_labor")
    assert any(index["name"] == "ix_subcontractor_weekly_labor_week_ending" and index["unique"] for index in indexes)


def test_reconciliation_rejects_incompatible_column(connection):
    connection.execute(sa.text("ALTER TABLE fabs ADD COLUMN is_migrated VARCHAR(10)"))
    with pytest.raises(RuntimeError, match="Incompatible definition for fabs.is_migrated"):
        migration.upgrade()


def test_reconciliation_rejects_incompatible_index(connection):
    migration.upgrade()
    connection.execute(sa.text("DROP INDEX ix_accounts_is_active"))
    connection.execute(sa.text("CREATE INDEX ix_accounts_is_active ON accounts (id)"))
    with pytest.raises(RuntimeError, match="Incompatible index ix_accounts_is_active"):
        migration.upgrade()


def test_reconciliation_refuses_to_guess_missing_required_values(connection):
    connection.execute(sa.text("CREATE TABLE performance_static_data (id INTEGER PRIMARY KEY)"))
    with pytest.raises(RuntimeError, match="Cannot safely reconstruct required column performance_static_data.year"):
        migration.upgrade()


def test_reconciliation_blocks_destructive_downgrade():
    with pytest.raises(RuntimeError, match="irreversible"):
        migration.downgrade()


def test_reconciliation_requires_online_connection(monkeypatch):
    monkeypatch.setattr(migration.context, "is_offline_mode", lambda: True)
    with pytest.raises(RuntimeError, match="online database connection"):
        migration.upgrade()


def test_reconciliation_preserves_and_repairs_partial_performance_table(connection):
    migration.upgrade()
    connection.execute(sa.text("INSERT INTO performance_static_data (year, total_wages) VALUES (2026, 45.5)"))
    connection.execute(sa.text("ALTER TABLE performance_static_data DROP COLUMN total_expenses"))
    migration.upgrade()
    assert connection.execute(sa.text("SELECT total_wages, total_expenses FROM performance_static_data")).one() == (45.5, None)


def test_reconciliation_repairs_missing_foreign_key(connection):
    if connection.dialect.name != "postgresql":
        pytest.skip("SQLite cannot add a foreign key to an existing table")
    migration.upgrade()
    foreign_key = sa.inspect(connection).get_foreign_keys("performance_static_data")[0]
    Operations(MigrationContext.configure(connection)).drop_constraint(
        foreign_key["name"], "performance_static_data", type_="foreignkey",
    )
    migration.upgrade()
    repaired = sa.inspect(connection).get_foreign_keys("performance_static_data")
    assert len(repaired) == 1
    assert repaired[0]["referred_table"] == "users"


def test_reconciliation_rolls_back_on_duplicate_financial_records(connection):
    table = migration._performance_tables()[0]
    table.create(connection)
    connection.execute(table.insert(), [{"year": 2026}, {"year": 2026}])
    with pytest.raises(sa.exc.IntegrityError):
        with connection.begin_nested():
            migration.upgrade()
    assert {column["name"] for column in sa.inspect(connection).get_columns("fabs")} == {"id"}
    assert "subcontractor_weekly_labor" not in sa.inspect(connection).get_table_names()
    assert connection.execute(sa.text("SELECT count(*) FROM performance_static_data")).scalar_one() == 2


def test_reconciliation_runs_after_server_merge_head(connection, tmp_path):
    versions = tmp_path / "versions"
    versions.mkdir()
    revisions = {
        "20261017_120000": None,
        "96ac9d3d1e92": None,
        "c3d4e5f67890": None,
        "043a0c77f7ac": ("20261017_120000", "96ac9d3d1e92", "c3d4e5f67890"),
    }
    for revision, parent in revisions.items():
        (versions / f"{revision}.py").write_text(
            f"revision = {revision!r}\ndown_revision = {parent!r}\ndef upgrade():\n    pass\n",
        )
    (versions / MIGRATION_PATH.name).write_text(MIGRATION_PATH.read_text())
    (tmp_path / "env.py").write_text(
        "from alembic import context\n"
        "context.configure(connection=context.config.attributes['connection'])\n"
        "with context.begin_transaction():\n"
        "    context.run_migrations()\n",
    )
    config = Config()
    config.set_main_option("script_location", str(tmp_path))
    config.attributes["connection"] = connection
    command.stamp(config, "043a0c77f7ac")
    command.upgrade(config, "heads")
    current = MigrationContext.configure(connection).get_current_heads()
    assert set(current) == {"043a0c77f7ac", "20261019_120000"}
    assert "performance_static_data" in sa.inspect(connection).get_table_names()