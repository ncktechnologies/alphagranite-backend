"""
Set cost_of_stone = 0 on migrated, install-complete FABs that have no cost.

Targets FABs with is_migrated = true, current_stage = 'install_completion' and
cost_of_stone IS NULL. Other FABs are left alone.

Run it after data_migration/migrate.py (and again after any re-run of it).

    python scripts/fill_migrated_cost_of_stone.py           # preview
    python scripts/fill_migrated_cost_of_stone.py --apply
"""
import argparse
import os
import sys

import psycopg2
from dotenv import load_dotenv

WHERE = "is_migrated AND current_stage = 'install_completion' AND cost_of_stone IS NULL"


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
    cur.execute(f"SELECT count(*) FROM fabs WHERE {WHERE}")
    print(f"Migrated install-complete FABs with no cost_of_stone: {cur.fetchone()[0]}")
    cur.execute("SELECT count(*) FROM fabs WHERE is_migrated AND cost_of_stone IS NULL"
                " AND current_stage IS DISTINCT FROM 'install_completion'")
    print(f"Migrated FABs with no cost_of_stone at other stages (left as-is): {cur.fetchone()[0]}")

    if not args.apply:
        print("\nPreview only. Re-run with --apply to set them to 0.")
        return
    cur.execute(f"UPDATE fabs SET cost_of_stone = 0 WHERE {WHERE}")
    conn.commit()
    print(f"\nSet cost_of_stone = 0 on {cur.rowcount} FABs.")


if __name__ == "__main__":
    main()
