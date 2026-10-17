"""Preview or set fabs.predraft_completed_date from the Caspio pre_draft_review date for selected FABs."""
import argparse
import csv
from datetime import datetime
import os
from pathlib import Path

from dotenv import load_dotenv
import psycopg2


DEFAULT_FAB_IDS = [14797, 15231, 15726, 15809, 15820, 15840, 15841, 15877, 15931, 15933, 15994, 16010]

# Caspio exports America/Chicago wall-clock times, which is how Odyssey stores timestamps.
DATE_FORMATS = ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %I:%M %p", "%m/%d/%Y")


def parse_caspio_datetime(value: str) -> datetime:
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date {value!r}")


def read_review_dates(path: Path, fab_ids: list[int]) -> dict[int, datetime]:
    wanted = set(fab_ids)
    dates = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        for required in ("fab_id", "pre_draft_review"):
            if (reader.fieldnames or []).count(required) != 1:
                raise ValueError(f"Expected exactly one {required!r} CSV column.")
        for record_number, row in enumerate(reader, start=2):
            raw_id = (row["fab_id"] or "").strip()
            if not raw_id.isdecimal() or int(raw_id) not in wanted:
                continue
            fab_id = int(raw_id)
            if fab_id in dates:
                raise ValueError(f"FAB {fab_id} appears more than once in the CSV.")
            raw_date = (row["pre_draft_review"] or "").strip()
            if not raw_date:
                raise ValueError(f"FAB {fab_id} has no pre_draft_review date (CSV record {record_number}).")
            try:
                dates[fab_id] = parse_caspio_datetime(raw_date)
            except ValueError as error:
                raise ValueError(f"FAB {fab_id}, CSV record {record_number}: {error}") from None
    missing = sorted(wanted - set(dates))
    if missing:
        raise ValueError(f"FABs not found in CSV; no changes applied: {missing}")
    return dates


def backfill(connection, dates: dict[int, datetime], *, apply=False):
    fab_ids = sorted(dates)
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout = '60s'")
        cursor.execute("SET LOCAL lock_timeout = '10s'")
        cursor.execute(
            "SELECT id, predraft_completed_date FROM public.fabs WHERE id = ANY(%s) ORDER BY id"
            + (" FOR UPDATE" if apply else ""),
            (fab_ids,),
        )
        current = dict(cursor.fetchall())
        missing = sorted(set(fab_ids) - set(current))
        if missing:
            raise ValueError(f"FABs missing from database; no changes applied: {missing}")

        changes = []
        print(f"{'FAB':>6}  {'current predraft_completed_date':<32} new (pre_draft_review)")
        for fab_id in fab_ids:
            old, new = current[fab_id], dates[fab_id]
            marker = "" if old == new else "  <- update"
            print(f"{fab_id:>6}  {str(old) if old else '(empty)':<32} {new}{marker}")
            if old != new:
                changes.append((new, fab_id))
        overwrites = sum(1 for _, fab_id in changes if current[fab_id] is not None)
        print(f"FABs to update: {len(changes)} of {len(fab_ids)}"
              + (f" ({overwrites} replace an existing date)" if overwrites else ""))
        if not apply or not changes:
            return
        for new, fab_id in changes:
            cursor.execute("UPDATE public.fabs SET predraft_completed_date = %s WHERE id = %s", (new, fab_id))
        print(f"Updated FABs: {len(changes)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True, help="Caspio Fab_Status export with a pre_draft_review column")
    parser.add_argument("--fab-ids", type=int, nargs="+", default=DEFAULT_FAB_IDS,
                        help="FAB ids to update (default: the 12 FABs this script was written for)")
    parser.add_argument("--expected-database", default="alpha_granite_production")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    load_dotenv()
    try:
        dates = read_review_dates(args.csv, args.fab_ids)
        url = os.getenv("DATABASE_URL")
        if not url:
            raise ValueError("DATABASE_URL is not configured.")
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
        url = url.replace("postgresql+psycopg2://", "postgresql://", 1)
        if Path("/.dockerenv").exists():
            url = url.replace("@localhost:", "@host.docker.internal:", 1)
        with psycopg2.connect(url, connect_timeout=10) as connection:
            connection.set_session(readonly=not args.apply)
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database()")
                database = cursor.fetchone()[0]
            if database != args.expected_database:
                raise ValueError(f"Wrong database: {database!r}; expected {args.expected_database!r}.")
            backfill(connection, dates, apply=args.apply)
        print("Changes committed." if args.apply else "Read-only preview. Run with --apply after reviewing.")
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"Error: {error}\n")
    except psycopg2.Error as error:
        parser.exit(1, f"Database operation failed; row changes rolled back. SQLSTATE: {error.pgcode or 'unavailable'}\n")


if __name__ == "__main__":
    main()
