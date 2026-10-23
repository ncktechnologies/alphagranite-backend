"""
Set status_id = 3 (Completed) on every business_job whose job_number is not in active_jobs.csv.

Job numbers are matched case-insensitively, ignoring surrounding spaces ("19954-A" only
matches "19954-A", not "19954"). Jobs already at status_id 3 are left alone, and listed jobs
are never changed (a listed job that is currently 3 is reported, not reopened).

The CSV may have blank rows above the header; the first row with a "job_number" cell is the
header. The database URL is DATABASE_URL from .env.production (use --env-file to pick another file).

    python scripts/complete_unlisted_jobs.py           # preview
    python scripts/complete_unlisted_jobs.py --apply
"""
import argparse
import csv
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

import psycopg2
from dotenv import dotenv_values

SCRIPTS_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = SCRIPTS_DIR / "active_jobs.csv"
DEFAULT_ENV = SCRIPTS_DIR.parent / ".env.production"
COMPLETED = 3
STATUS_NAMES = {0: "Inactive", 1: "Active", 3: "Completed"}


def read_job_numbers(path: Path) -> dict[str, str]:
    """Lower-cased job number -> job number as written in the CSV."""
    if not path.exists():
        sys.exit(f"CSV not found: {path}")
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    header_index = next(
        (i for i, row in enumerate(rows) if any(cell.strip().lower() == "job_number" for cell in row)),
        None,
    )
    if header_index is None:
        sys.exit(f"{path} has no 'job_number' column")
    column = [cell.strip().lower() for cell in rows[header_index]].index("job_number")
    numbers = {
        row[column].strip().lower(): row[column].strip()
        for row in rows[header_index + 1:]
        if len(row) > column and row[column].strip()
    }
    if not numbers:
        sys.exit(f"{path} has no job numbers; refusing to complete every job")
    return numbers


def database_url(env_file: Path) -> str:
    if not env_file.exists():
        sys.exit(f"Env file not found: {env_file}")
    url = dotenv_values(env_file).get("DATABASE_URL")
    if not url:
        sys.exit(f"DATABASE_URL not set in {env_file}")
    url = url.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")
    if os.path.exists("/.dockerenv"):
        url = url.replace("@localhost:", "@host.docker.internal:", 1)
    return url


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Active jobs CSV (default: scripts/active_jobs.csv)")
    ap.add_argument("--env-file", type=Path, default=DEFAULT_ENV, help="Env file with DATABASE_URL (default: .env.production)")
    ap.add_argument("--apply", action="store_true", help="Write the changes (default: preview)")
    ap.add_argument("--show", type=int, default=50, help="How many jobs to list in the preview (default: 50, 0 for all)")
    args = ap.parse_args()

    csv_numbers = read_job_numbers(args.csv)
    active_numbers = sorted(csv_numbers)
    url = database_url(args.env_file)
    target = urlsplit(url)
    print(f"Database: {target.path.lstrip('/')} on {target.hostname}:{target.port or 5432}")
    print(f"CSV: {args.csv} ({len(active_numbers)} job numbers)")

    conn = psycopg2.connect(url, connect_timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT id, job_number, name, status_id FROM business_jobs ORDER BY id")
    jobs = cur.fetchall()

    def listed(job_number):
        return (job_number or "").strip().lower() in active_numbers

    to_complete = [job for job in jobs if not listed(job[1]) and job[3] != COMPLETED]
    already_completed = sum(1 for job in jobs if not listed(job[1]) and job[3] == COMPLETED)
    listed_jobs = [job for job in jobs if listed(job[1])]
    listed_but_completed = [job[1] for job in listed_jobs if job[3] == COMPLETED]
    found = {(job[1] or "").strip().lower() for job in listed_jobs}
    missing = [csv_numbers[n] for n in active_numbers if n not in found]

    print(f"Jobs in database: {len(jobs)}")
    print(f"  in the CSV (kept as they are):        {len(listed_jobs)}")
    print(f"  not in the CSV, already Completed:    {already_completed}")
    print(f"  not in the CSV, to set to Completed:  {len(to_complete)}")
    by_status = Counter(STATUS_NAMES.get(job[3], f"status {job[3]}") for job in to_complete)
    for status_name, count in sorted(by_status.items()):
        print(f"    from {status_name}: {count}")

    shown = to_complete if args.show == 0 else to_complete[:args.show]
    for job_id, job_number, name, status_id in shown:
        print(f"    {job_id:6d}  {job_number or '-':<10}  status {status_id} -> {COMPLETED}  {name or ''}")
    if len(shown) < len(to_complete):
        print(f"    ... and {len(to_complete) - len(shown)} more (use --show 0 to list all)")

    if listed_but_completed:
        print(f"CSV jobs currently Completed (not changed): {', '.join(sorted(listed_but_completed))}")
    if missing:
        print(f"CSV job numbers with no matching job: {', '.join(missing)}")

    now = datetime.now(ZoneInfo("America/Chicago")).replace(tzinfo=None)
    cur.execute(
        "UPDATE business_jobs SET status_id = %s, updated_at = %s"
        " WHERE lower(trim(coalesce(job_number, ''))) <> ALL(%s) AND status_id IS DISTINCT FROM %s",
        (COMPLETED, now, active_numbers, COMPLETED),
    )
    updated = cur.rowcount

    if not args.apply:
        conn.rollback()
        print(f"\nPreview only (rolled back {updated} updates). Re-run with --apply to write.")
        return
    conn.commit()
    print(f"\nApplied: {updated} jobs set to status_id {COMPLETED} (Completed).")


if __name__ == "__main__":
    main()
