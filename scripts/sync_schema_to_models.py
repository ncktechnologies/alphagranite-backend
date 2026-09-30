"""
Bring a database's schema up to the current SQLModel models, then stamp
alembic_version at head.

For databases whose alembic history is broken (unknown or server-only
revisions). Instead of generating a migration file (a server-only migration is
what caused the problem), this compares the live schema with the models exactly
as `alembic revision --autogenerate` would, and:

  applies  missing tables, missing columns, missing indexes
  reports  everything else (drops, type/nullability changes, removed indexes)
           without touching it

Column types are not compared: every datetime column is `timestamp` by design
(America/Chicago wall-clock), while the models map datetimes to a timezone-aware
type, so a type comparison would propose converting ~236 columns.

Only structure is synced; data backfills inside skipped migrations do not run.

    python scripts/sync_schema_to_models.py            # preview
    python scripts/sync_schema_to_models.py --apply    # apply + stamp head (one transaction)
"""
import argparse
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import DefaultClause, create_engine, text

# Project root; the cwd (/app in the container) when piped in with `python -`.
_this = globals().get("__file__", "<stdin>")
ROOT = os.getcwd() if _this == "<stdin>" else os.path.abspath(os.path.join(os.path.dirname(_this), ".."))
sys.path.insert(0, ROOT)

ADDITIVE = ("add_table", "add_column", "add_index")
KEEP_TABLES = {"migration_rejects", "unresolved_references"}  # Caspio import audit, not models


def load_models():
    """Register models exactly as alembic/env.py does (its import section)."""
    env_py = os.path.join(ROOT, "alembic", "env.py")
    source = open(env_py).read().split("config = context.config", 1)[0]
    namespace = {"__file__": env_py}
    exec(compile(source, env_py, "exec"), namespace)
    return namespace["SQLModel"].metadata


def head_revision():
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    heads = ScriptDirectory.from_config(Config(os.path.join(ROOT, "alembic.ini"))).get_heads()
    if len(heads) != 1:
        sys.exit(f"alembic/versions has {len(heads)} heads {heads}; move server-only files out first.")
    return heads[0]


def make_addable(column):
    """A NOT NULL column added to a table with rows needs a DB default: use the
    model's scalar default, else add it as nullable. Returns a note or None."""
    if column.nullable or column.server_default is not None:
        return None
    default = column.default
    if default is not None and getattr(default, "is_scalar", False):
        value = default.arg
        if isinstance(value, bool):
            literal = "true" if value else "false"
        elif isinstance(value, (int, float)):
            literal = str(value)
        else:
            literal = "'" + str(value).replace("'", "''") + "'"
        column.server_default = DefaultClause(text(literal))
        return f"(NOT NULL, existing rows get {literal})"
    column.nullable = True
    return "(model says NOT NULL but has no default: added as NULLABLE, backfill by hand)"


def describe(diff):
    kind = diff[0]
    if kind in ("add_table", "remove_table"):
        return f"{kind:14s} {diff[1].name}"
    if kind in ("add_column", "remove_column"):
        return f"{kind:14s} {diff[2]}.{diff[3].name}"
    if kind in ("add_index", "remove_index"):
        return f"{kind:14s} {diff[1].name} on {diff[1].table.name}"
    if kind.startswith("modify_"):
        return f"{kind:14s} {diff[2]}.{diff[3]}: {diff[-2]!r} -> {diff[-1]!r}"
    return f"{kind:14s} {diff[1]!r}"[:160]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="Apply additive changes and stamp head")
    args = ap.parse_args()

    load_dotenv(os.path.join(ROOT, ".env"))
    url = os.getenv("DATABASE_URL")
    if not url:
        sys.exit("DATABASE_URL not set")
    url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://").replace("postgresql://", "postgresql+psycopg2://", 1)
    if os.path.exists("/.dockerenv"):
        url = url.replace("@localhost:", "@host.docker.internal:", 1)

    from alembic.autogenerate import compare_metadata, produce_migrations
    from alembic.migration import MigrationContext
    from alembic.operations import Operations, ops

    metadata = load_models()
    head = head_revision()
    engine = create_engine(url)
    with engine.begin() as conn:
        current = [r[0] for r in conn.execute(text("SELECT version_num FROM alembic_version"))]
        print(f"alembic_version now: {', '.join(current) or '(empty)'}   head: {head}")

        opts = {"compare_type": False,
                "include_object": lambda obj, name, type_, reflected, compare_to:
                    not (type_ == "table" and name in KEEP_TABLES)}
        ctx = MigrationContext.configure(conn, opts=opts)
        diffs = []
        for d in compare_metadata(ctx, metadata):
            diffs.extend(d if isinstance(d, list) else [d])
        additive = [d for d in diffs if d[0] in ADDITIVE]
        other = [d for d in diffs if d[0] not in ADDITIVE]

        print(f"\nWill apply ({len(additive)}):")
        for d in additive:
            note = make_addable(d[3]) if d[0] == "add_column" else None
            print("  " + describe(d) + (f"  {note}" if note else ""))
        print(f"\nWill NOT apply, review by hand ({len(other)}):")
        for d in other:
            print("  " + describe(d))

        if not args.apply:
            print("\nPreview only. Re-run with --apply to apply the additive changes and stamp head.")
            return

        # Run the same operations autogenerate would write, additive ones only.
        operations = Operations(ctx)
        script = produce_migrations(ctx, metadata)

        def additive_ops(op_list):
            for op in op_list:
                if isinstance(op, ops.ModifyTableOps):
                    yield from (o for o in op.ops if isinstance(o, (ops.AddColumnOp, ops.CreateIndexOp)))
                elif isinstance(op, (ops.CreateTableOp, ops.CreateIndexOp)):
                    yield op

        def index_exists(name):
            return conn.execute(text("SELECT 1 FROM pg_indexes WHERE schemaname='public'"
                                     " AND indexname=:n"), {"n": name}).first() is not None

        applied = 0
        for op in additive_ops(script.upgrade_ops.ops):
            # Adding an index=True column already creates its index.
            if isinstance(op, ops.CreateIndexOp) and index_exists(op.index_name):
                continue
            operations.invoke(op)
            applied += 1
        conn.execute(text("DELETE FROM alembic_version"))
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES (:v)"), {"v": head})
        print(f"\nApplied {applied} change(s); alembic_version stamped at {head}.")


if __name__ == "__main__":
    main()
