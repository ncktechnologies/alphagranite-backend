"""Create missing completed CNC records for CSV FABs with a section-1 shop plan."""
import argparse
import csv
from datetime import datetime
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
import psycopg2


def read_csv_fab_ids(path: Path) -> list[int]:
    fab_ids = set()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        if (reader.fieldnames or []).count("fab_id") != 1:
            raise ValueError("Expected exactly one 'fab_id' CSV column.")
        for record_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Unexpected column count in CSV record {record_number}.")
            raw_id = row["fab_id"].strip()
            if not raw_id.isascii() or not raw_id.isdecimal() or int(raw_id) <= 0:
                raise ValueError(f"Invalid fab_id in CSV record {record_number}.")
            fab_ids.add(int(raw_id))
    return sorted(fab_ids)


def backfill(connection, fab_ids, *, apply=False, drafter_id=None):
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout = '120s'")
        cursor.execute("SET LOCAL lock_timeout = '10s'")
        cursor.execute("SET LOCAL TIME ZONE 'America/Chicago'")
        if apply:
            cursor.execute("LOCK TABLE public.fabs, public.shop_cut_plans IN SHARE MODE")
            cursor.execute("LOCK TABLE public.cnc_draftings IN SHARE ROW EXCLUSIVE MODE")
        cursor.execute("SELECT id FROM public.fabs WHERE id = ANY(%s) ORDER BY id", (fab_ids,))
        found_ids = [row[0] for row in cursor.fetchall()]
        missing_ids = sorted(set(fab_ids) - set(found_ids))
        if missing_ids:
            raise ValueError(f"CSV FABs missing from database; no changes applied: {missing_ids}")
        cursor.execute(
            "SELECT f.id FROM public.fabs f WHERE f.id = ANY(%s) AND EXISTS ("
            "SELECT 1 FROM public.shop_cut_plans p "
            "WHERE p.fab_id = f.id AND p.planning_section_id = 1) ORDER BY f.id",
            (fab_ids,),
        )
        eligible_ids = [row[0] for row in cursor.fetchall()]
        cursor.execute(
            "SELECT DISTINCT fab_id FROM public.cnc_draftings WHERE fab_id = ANY(%s)",
            (eligible_ids,),
        )
        existing_ids = {row[0] for row in cursor.fetchall()}
        insert_ids = sorted(set(eligible_ids) - existing_ids)
        print(f"CSV FABs: {len(found_ids)}; with section-1 plans: {len(eligible_ids)}")
        print(f"Existing CNC FABs left unchanged: {len(existing_ids)}; missing records to create: {len(insert_ids)}")
        print(f"FAB IDs to create: {insert_ids}")
        if not insert_ids:
            return []
        if drafter_id is None:
            cursor.execute("SELECT id FROM public.users WHERE username = %s ORDER BY id LIMIT 1", ("migration_bot",))
        else:
            cursor.execute("SELECT id FROM public.users WHERE id = %s", (drafter_id,))
        drafter = cursor.fetchone()
        if not drafter:
            raise ValueError("No valid drafter found. Supply an existing user with --drafter-id.")
        drafter_id = drafter[0]
        cursor.execute("SELECT value_id FROM public.status WHERE value_id = 3 LIMIT 1")
        if not cursor.fetchone():
            raise ValueError("CNC completed status_id=3 is not configured in the status table.")
        print(f"New records: drafter_id={drafter_id}, is_completed=true, status_id=3")
        if not apply:
            return insert_ids
        now = datetime.now(ZoneInfo("America/Chicago")).replace(tzinfo=None)
        note = (
            "CSV maintenance backfill: existing planning_section_id=1 shop plan; "
            "CNC marked completed as requested. Scheduling dates are placeholders "
            "set to the backfill run time, not historical production dates."
        )
        cursor.execute(
            "INSERT INTO public.cnc_draftings ("
            "drafter_id, fab_id, scheduled_start_date, scheduled_end_date, "
            "total_sqft_required_to_draft, created_at, is_completed, status_id, "
            "cad_review_complete, draft_completed, updated_at, updated_by, notes) "
            "SELECT %s, f.id, %s, %s, COALESCE(f.total_sqft, 0)::text, %s, true, 3, "
            "false, true, %s, %s, %s FROM public.fabs f WHERE f.id = ANY(%s) "
            "AND NOT EXISTS (SELECT 1 FROM public.cnc_draftings c WHERE c.fab_id = f.id) "
            "RETURNING fab_id",
            (drafter_id, now, now, now, now, drafter_id, note, insert_ids),
        )
        created_ids = sorted(row[0] for row in cursor.fetchall())
        print(f"Created completed CNC records: {len(created_ids)}")
        return created_ids


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--expected-database", default="alpha_granite_production")
    parser.add_argument("--drafter-id", type=int, help="Existing user; defaults to migration_bot")
    parser.add_argument("--apply", action="store_true", help="Commit inserts; default is read-only preview")
    args = parser.parse_args()
    load_dotenv()
    try:
        fab_ids = read_csv_fab_ids(args.csv)
        if not fab_ids:
            print("CSV contains no FABs; nothing to change.")
            return
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
            backfill(connection, fab_ids, apply=args.apply, drafter_id=args.drafter_id)
        print("Changes committed." if args.apply else "Read-only preview. Run with --apply after reviewing and backing up.")
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"Error: {error}\n")
    except psycopg2.Error as error:
        parser.exit(1, f"Database operation failed; row changes rolled back. SQLSTATE: {error.pgcode or 'unavailable'}\n")


if __name__ == "__main__":
    main()