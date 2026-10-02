"""
Remove everything the Caspio data migration created, so it can be re-run with
new data.

Deletes, in one transaction:
  1. Migrated FABs (is_migrated, or created by migration_bot for imports made
     before the flag existed) and every row that depends on them: anything
     pointing at them through a foreign key or a fab_id column, recursively.
     That includes rows users added later to an imported FAB (notes, files,
     timers, ...).
  2. Jobs the migration created that no longer have any FABs, with their
     dependent rows (job_id references).
  3. Accounts, stone types/colors/thickness, edges, work stations and planning
     sections created by migration_bot that nothing references any more, plus
     numeric fab_type names ("1", "3", ...) no FAB uses.
  4. The migration's own log tables: migration_rejects, unresolved_references.

Data created in the app (users, roles, FABs/jobs that were not imported, and
anything they still reference) is kept. The migration_bot user is kept.

    python scripts/scrub_migrated_data.py                         # preview (rolled back)
    python scripts/scrub_migrated_data.py --apply --confirm-db NAME

Take a pg_dump first.
"""
import argparse
import os
import sys
from collections import Counter, defaultdict

import psycopg2
from dotenv import load_dotenv

MIG_USER = "migration_bot"
# Created by the migration through created_by; removed only when unreferenced.
REFERENCE_TABLES = ["stone_colors", "stone_types", "stone_thickness", "edges",
                    "work_stations", "planning_sections", "accounts"]
LOG_TABLES = ["migration_rejects", "unresolved_references"]
# fab_id / job_id columns without a foreign key still point at these.
IMPLICIT_PARENTS = {"fab_id": "fabs", "job_id": "business_jobs"}


class Scrubber:
    def __init__(self, cur):
        self.cur = cur
        self.deleted = Counter()
        self.children = defaultdict(set)  # parent table -> {(child table, child column)}
        self._load_relations()

    def _load_relations(self):
        self.cur.execute("""
            SELECT c.conrelid::regclass::text, a.attname, c.confrelid::regclass::text
            FROM pg_constraint c
            JOIN LATERAL unnest(c.conkey) WITH ORDINALITY k(attnum, n) ON true
            JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum
            WHERE c.contype = 'f' AND c.connamespace = 'public'::regnamespace
              AND array_length(c.conkey, 1) = 1""")
        for child, col, parent in self.cur.fetchall():
            self.children[parent].add((child, col))
        self.cur.execute("""
            SELECT table_name, column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND column_name = ANY(%s)""", (list(IMPLICIT_PARENTS),))
        for table, col in self.cur.fetchall():
            parent = IMPLICIT_PARENTS[col]
            if table != parent:
                self.children[parent].add((table, col))

    def cascade_delete(self, table, condition, params=(), path=()):
        """Delete rows of `table` matching `condition`, dependents first."""
        if table in path:  # cycle guard
            return
        for child, col in sorted(self.children.get(table, ())):
            if child == table:
                continue
            self.cascade_delete(
                child, f'"{col}" IN (SELECT id FROM "{table}" WHERE {condition})',
                params, path + (table,))
        self.cur.execute(f'DELETE FROM "{table}" WHERE {condition}', params)
        self.deleted[table] += self.cur.rowcount

    def delete_unreferenced(self, table, condition, params=()):
        """Delete rows nothing points at (by foreign key or fab_id/job_id)."""
        refs = " AND ".join(
            f'NOT EXISTS (SELECT 1 FROM "{child}" r WHERE r."{col}" = t.id)'
            for child, col in sorted(self.children.get(table, ())) if child != table) or "true"
        self.cur.execute(f'DELETE FROM "{table}" t WHERE ({condition}) AND {refs}', params)
        self.deleted[table] += self.cur.rowcount
        return self.cur.rowcount


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="Commit the deletes (default: preview)")
    ap.add_argument("--confirm-db", help="Name of the database being scrubbed; required with --apply")
    args = ap.parse_args()

    load_dotenv()
    url = os.getenv("DATABASE_URL")
    if not url:
        sys.exit("DATABASE_URL not set")
    url = url.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")
    if os.path.exists("/.dockerenv"):
        url = url.replace("@localhost:", "@host.docker.internal:", 1)

    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute("SELECT current_database()")
    db_name = cur.fetchone()[0]
    cur.execute("SELECT id FROM users WHERE username = %s", (MIG_USER,))
    row = cur.fetchone()
    if not row:
        sys.exit(f"No {MIG_USER} user in {db_name}: nothing was imported here.")
    mig = row[0]
    cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.columns"
                " WHERE table_name = 'fabs' AND column_name = 'is_migrated')")
    has_flag = cur.fetchone()[0]

    s = Scrubber(cur)
    fab_cond = ("is_migrated OR created_by = %s" if has_flag else "created_by = %s")
    cur.execute(f"SELECT count(*) FROM fabs WHERE {fab_cond}", (mig,))
    print(f"Database: {db_name}   migrated FABs: {cur.fetchone()[0]}\n")

    # 1. migrated FABs and everything hanging off them
    s.cascade_delete("fabs", fab_cond, (mig,))
    # 2. migrated jobs left without FABs
    s.cascade_delete("business_jobs",
                     "created_by = %s AND NOT EXISTS (SELECT 1 FROM fabs f WHERE f.job_id = business_jobs.id)",
                     (mig,))
    # 3. reference rows the migration created and nothing uses now (repeat for chains)
    while sum(s.delete_unreferenced(t, "t.created_by = %s", (mig,)) for t in REFERENCE_TABLES):
        pass
    cur.execute("DELETE FROM fab_type t WHERE t.name ~ '^\\s*[0-9]+\\s*$'"
                " AND NOT EXISTS (SELECT 1 FROM fabs f WHERE trim(f.fab_type) = trim(t.name))")
    s.deleted["fab_type"] += cur.rowcount
    # 4. migration log tables
    for t in LOG_TABLES:
        cur.execute("SELECT to_regclass(%s)", (t,))
        if cur.fetchone()[0]:
            cur.execute(f'DELETE FROM "{t}"')
            s.deleted[t] += cur.rowcount

    print("Rows deleted:")
    for table, n in sorted(s.deleted.items(), key=lambda kv: -kv[1]):
        if n:
            print(f"  {table:40s} {n:>8}")
    print(f"  {'TOTAL':40s} {sum(s.deleted.values()):>8}")

    if not args.apply:
        conn.rollback()
        print(f"\nPreview only (rolled back). To scrub: --apply --confirm-db {db_name}")
        return
    if args.confirm_db != db_name:
        conn.rollback()
        sys.exit(f"\nRefusing: --confirm-db must be exactly '{db_name}'. Nothing deleted.")
    conn.commit()
    print("\nScrubbed. The migration can be re-run.")


if __name__ == "__main__":
    main()
