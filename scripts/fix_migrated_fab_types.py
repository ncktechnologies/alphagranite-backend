"""
Replace Caspio fab type IDs with their names on migrated FABs.

Caspio's Fab_Status.fab_type holds the Fab_Types id ("1", "3", ...), so the
data migration stores those ids in fabs.fab_type. This sets the name instead
(1 -> STANDARD, ...) on FABs with is_migrated = true, makes sure each name
exists in the fab_type lookup table, and removes the numeric lookup rows the
import created once no FAB uses them.

Run it after data_migration/migrate.py (and again after any re-run of it).

    python scripts/fix_migrated_fab_types.py           # preview
    python scripts/fix_migrated_fab_types.py --apply
"""
import argparse
import os
import sys

import psycopg2
from dotenv import load_dotenv

# Caspio Fab_Types (fab_type_id -> fab_type).
FAB_TYPES = {
    "1": "STANDARD",
    "2": "FAB ONLY",
    "3": "AG REDO",
    "4": "CUST REDO",
    "5": "RESURFACE",
    "7": "FAST TRACK",
    "8": "BASIC",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="Write the changes (default: preview)")
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
    ids = list(FAB_TYPES)

    cur.execute("SELECT trim(fab_type), count(*) FROM fabs WHERE is_migrated"
                " AND trim(fab_type) = ANY(%s) GROUP BY 1 ORDER BY 1", (ids,))
    to_fix = cur.fetchall()
    cur.execute("SELECT DISTINCT fab_type FROM fabs WHERE is_migrated AND fab_type ~ '^\\s*[0-9]+\\s*$'"
                " AND trim(fab_type) <> ALL(%s)", (ids,))
    unknown = [r[0] for r in cur.fetchall()]

    print("Migrated FABs to update:")
    for type_id, n in to_fix:
        print(f"  {type_id:>3} -> {FAB_TYPES[type_id]:12s} {n:6d} fabs")
    print(f"  total {sum(n for _, n in to_fix)}")
    if unknown:
        print(f"Numeric fab types with no mapping (left as-is): {', '.join(unknown)}")

    for type_id, name in FAB_TYPES.items():
        cur.execute("UPDATE fabs SET fab_type=%s WHERE is_migrated AND trim(fab_type)=%s",
                    (name, type_id))
    for name in FAB_TYPES.values():
        cur.execute("INSERT INTO fab_type(name, created_at) SELECT %s, now()"
                    " WHERE NOT EXISTS (SELECT 1 FROM fab_type WHERE upper(name)=upper(%s))",
                    (name, name))
    cur.execute("DELETE FROM fab_type t WHERE trim(t.name) = ANY(%s)"
                " AND NOT EXISTS (SELECT 1 FROM fabs f WHERE trim(f.fab_type) = trim(t.name))"
                " RETURNING t.name", (ids,))
    removed = sorted(r[0] for r in cur.fetchall())
    print(f"fab_type lookup rows removed: {', '.join(removed) or 'none'}")

    if not args.apply:
        conn.rollback()
        print("\nPreview only (rolled back). Re-run with --apply to write.")
        return
    conn.commit()
    print("\nApplied.")


if __name__ == "__main__":
    main()
