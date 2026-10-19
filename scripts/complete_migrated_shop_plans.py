"""
Mark shop cut plans complete on migrated FABs that Caspio shows as finished.

A FAB qualifies when its Caspio Fab_Status row has fab_percent = 100 and the
migrated FAB (fabs.id = Caspio fab_id, is_migrated = true) has
shop_est_completion_date set. Every shop_cut_plans row of a qualifying FAB that
is below 100% is set to work_percentage = 100. Other columns (including
actual_end_date) are left as they are.

Run it after data_migration/migrate.py (and again after any re-run of it).

    python scripts/complete_migrated_shop_plans.py           # preview
    python scripts/complete_migrated_shop_plans.py --apply
    python scripts/complete_migrated_shop_plans.py --csv path/to/Fab_Status_....csv --list
"""
import argparse
import csv
import glob
import os
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

CSV_DIR = os.path.join(os.path.dirname(__file__), "..", "data_migration", "actual_caspio_data_csv")


def default_csv():
    paths = sorted(glob.glob(os.path.join(CSV_DIR, "Fab_Status_*.csv")))
    return paths[-1] if paths else None


def fab_ids_at_100(path):
    """Caspio fab_ids whose fab_percent is 100 (or more)."""
    ids, rows = set(), 0
    with open(path, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            rows += 1
            try:
                fab_id = int(Decimal((r.get("fab_id") or "").strip()))
                pct = Decimal((r.get("fab_percent") or "").strip())
            except InvalidOperation:
                continue
            if pct >= 100:
                ids.add(fab_id)
    return ids, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default=default_csv(), help="Caspio Fab_Status export (default: newest in data_migration/actual_caspio_data_csv)")
    ap.add_argument("--apply", action="store_true", help="Write the changes (default: preview)")
    ap.add_argument("--list", action="store_true", help="Print every FAB id that will be updated")
    args = ap.parse_args()

    if not args.csv or not os.path.exists(args.csv):
        sys.exit(f"Fab_Status CSV not found: {args.csv}")

    load_dotenv()
    url = os.getenv("DATABASE_URL")
    if not url:
        sys.exit("DATABASE_URL not set")
    url = url.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")
    if os.path.exists("/.dockerenv"):
        url = url.replace("@localhost:", "@host.docker.internal:", 1)

    done_ids, csv_rows = fab_ids_at_100(args.csv)
    print(f"CSV: {args.csv}")
    print(f"  Fab_Status rows: {csv_rows}, with fab_percent = 100: {len(done_ids)}")

    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute("CREATE TEMP TABLE caspio_done (fab_id integer PRIMARY KEY) ON COMMIT DROP")
    execute_values(cur, "INSERT INTO caspio_done (fab_id) VALUES %s", [(i,) for i in done_ids])

    # Why each fab_percent = 100 FAB does or doesn't get updated.
    cur.execute("""
        SELECT
            count(*) FILTER (WHERE f.id IS NULL),
            count(*) FILTER (WHERE f.id IS NOT NULL AND f.shop_est_completion_date IS NULL),
            count(*) FILTER (WHERE f.shop_est_completion_date IS NOT NULL AND p.total IS NULL),
            count(*) FILTER (WHERE f.shop_est_completion_date IS NOT NULL AND p.open = 0),
            count(*) FILTER (WHERE f.shop_est_completion_date IS NOT NULL AND p.open > 0)
        FROM caspio_done c
        LEFT JOIN fabs f ON f.id = c.fab_id AND f.is_migrated
        LEFT JOIN (
            SELECT fab_id, count(*) AS total,
                   count(*) FILTER (WHERE coalesce(work_percentage, 0) < 100) AS open
            FROM shop_cut_plans GROUP BY fab_id
        ) p ON p.fab_id = f.id
    """)
    missing, no_est_date, no_plans, already_done, to_update = cur.fetchone()
    print("FABs with fab_percent = 100:")
    print(f"  not a migrated FAB in Odyssey          {missing:6d}  (skipped)")
    print(f"  no shop_est_completion_date            {no_est_date:6d}  (skipped)")
    print(f"  no shop cut plans                      {no_plans:6d}  (skipped)")
    print(f"  all shop cut plans already at 100%     {already_done:6d}  (nothing to do)")
    print(f"  with shop cut plans below 100%         {to_update:6d}  (will update)")

    target = """
        FROM shop_cut_plans p
        JOIN fabs f ON f.id = p.fab_id
        JOIN caspio_done c ON c.fab_id = f.id
        WHERE f.is_migrated
          AND f.shop_est_completion_date IS NOT NULL
          AND coalesce(p.work_percentage, 0) < 100
    """
    cur.execute(f"""
        SELECT count(*), count(*) FILTER (WHERE p.actual_end_date IS NULL),
               coalesce(array_agg(DISTINCT p.fab_id ORDER BY p.fab_id), '{{}}')
        {target}
    """)
    plan_count, no_end_date, fab_ids = cur.fetchone()
    print(f"Shop cut plans to set to 100%: {plan_count}")
    if no_end_date:
        print(f"  {no_end_date} of them have no actual_end_date (left as-is)")
    if fab_ids:
        shown = fab_ids if args.list else fab_ids[:20]
        more = "" if args.list or len(fab_ids) <= 20 else f" ... (+{len(fab_ids) - 20} more, use --list)"
        print(f"  FAB ids: {', '.join(map(str, shown))}{more}")

    now = datetime.now(ZoneInfo("America/Chicago")).replace(tzinfo=None)
    cur.execute(f"""
        UPDATE shop_cut_plans SET work_percentage = 100, updated_at = %s
        WHERE id IN (SELECT p.id {target})
    """, (now,))
    updated = cur.rowcount

    if not args.apply:
        conn.rollback()
        print(f"\nPreview only (rolled back {updated} updates). Re-run with --apply to write.")
        return
    conn.commit()
    print(f"\nApplied: {updated} shop cut plans set to 100%.")


if __name__ == "__main__":
    main()
