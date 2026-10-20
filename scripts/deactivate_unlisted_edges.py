"""
Set status_id = 0 on every edge whose name is not in EdgeListforOdyssey.csv.

Names are matched case-insensitively, ignoring surrounding spaces. Edges already
at status_id 0 are left alone, and listed edges are never changed (an edge in
the CSV that is currently 0 is reported, not reactivated).

The database URL is DATABASE_URL from .env.production (use --env-file to pick
another file).

    python scripts/deactivate_unlisted_edges.py           # preview
    python scripts/deactivate_unlisted_edges.py --apply
"""
import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

import psycopg2
from dotenv import dotenv_values

SCRIPTS_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = SCRIPTS_DIR / "EdgeListforOdyssey.csv"
DEFAULT_ENV = SCRIPTS_DIR.parent / ".env.production"


def read_edge_names(path: Path) -> set[str]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if "name" not in (reader.fieldnames or []):
            sys.exit(f"{path} has no 'name' column")
        names = {(row["name"] or "").strip().lower() for row in reader}
    names.discard("")
    if not names:
        sys.exit(f"{path} has no edge names; refusing to deactivate every edge")
    return names


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
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Edge list CSV (default: scripts/EdgeListforOdyssey.csv)")
    ap.add_argument("--env-file", type=Path, default=DEFAULT_ENV, help="Env file with DATABASE_URL (default: .env.production)")
    ap.add_argument("--apply", action="store_true", help="Write the changes (default: preview)")
    args = ap.parse_args()

    valid_names = sorted(read_edge_names(args.csv))
    url = database_url(args.env_file)
    target = urlsplit(url)
    print(f"Database: {target.path.lstrip('/')} on {target.hostname}:{target.port or 5432}")
    print(f"CSV: {args.csv} ({len(valid_names)} edge names)")

    conn = psycopg2.connect(url, connect_timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT id, name, status_id FROM edges ORDER BY name")
    edges = cur.fetchall()
    listed = {name.strip().lower() for _, name, _ in edges}

    to_deactivate = [(i, n, s) for i, n, s in edges if n.strip().lower() not in valid_names and s != 0]
    already_zero = sum(1 for _, n, s in edges if n.strip().lower() not in valid_names and s == 0)
    listed_but_zero = [n for _, n, s in edges if n.strip().lower() in valid_names and s == 0]
    missing = [n for n in valid_names if n not in listed]

    print(f"Edges in database: {len(edges)}")
    print(f"  in the CSV (kept as they are):     {len(edges) - len(to_deactivate) - already_zero}")
    print(f"  not in the CSV, already status 0:  {already_zero}")
    print(f"  not in the CSV, to set to 0:       {len(to_deactivate)}")
    for edge_id, name, status_id in to_deactivate:
        print(f"    {edge_id:6d}  status {status_id} -> 0  {name}")
    if listed_but_zero:
        print(f"CSV edges currently at status 0 (not changed): {', '.join(listed_but_zero)}")
    if missing:
        print(f"CSV names with no matching edge: {', '.join(missing)}")

    now = datetime.now(ZoneInfo("America/Chicago")).replace(tzinfo=None)
    cur.execute(
        "UPDATE edges SET status_id = 0, updated_at = %s"
        " WHERE lower(trim(name)) <> ALL(%s) AND status_id <> 0",
        (now, valid_names),
    )
    updated = cur.rowcount

    if not args.apply:
        conn.rollback()
        print(f"\nPreview only (rolled back {updated} updates). Re-run with --apply to write.")
        return
    conn.commit()
    print(f"\nApplied: {updated} edges set to status_id 0.")


if __name__ == "__main__":
    main()
