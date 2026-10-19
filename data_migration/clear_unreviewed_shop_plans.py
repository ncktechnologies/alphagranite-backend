"""Preview or remove shop plans and shop estimates for CSV FABs with unfinished pre-shop review."""
import argparse
import csv
import os
from pathlib import Path

from dotenv import load_dotenv
import psycopg2


FALSE_VALUES = {"0", "false", "f", "no", "n"}


def read_target_fab_ids(path: Path) -> list[int]:
    targets = set()
    flags_by_id = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        for required in ("fab_id", "pre_shop_review_completed"):
            if (reader.fieldnames or []).count(required) != 1:
                raise ValueError(f"Expected exactly one {required!r} CSV column.")
        for record_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Unexpected column count in CSV record {record_number}.")
            flag = row["pre_shop_review_completed"].strip().lower()
            raw_id = row["fab_id"].strip()
            if not raw_id.isascii() or not raw_id.isdecimal() or int(raw_id) <= 0:
                raise ValueError(f"Invalid fab_id in CSV record {record_number}.")
            fab_id = int(raw_id)
            is_target = flag in FALSE_VALUES
            if fab_id in flags_by_id and flags_by_id[fab_id] != is_target:
                raise ValueError(f"Conflicting pre-shop review values for FAB {fab_id}.")
            flags_by_id[fab_id] = is_target
            if is_target:
                targets.add(fab_id)
    return sorted(targets)


def cleanup(connection, fab_ids, *, apply=False, delete_timer_history=False, detach_files=False):
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout = '120s'")
        cursor.execute("SET LOCAL lock_timeout = '10s'")
        if apply:
            cursor.execute("LOCK TABLE public.fabs, public.shop_cut_plans IN SHARE ROW EXCLUSIVE MODE")
        cursor.execute("SELECT id FROM public.fabs WHERE id = ANY(%s) ORDER BY id", (fab_ids,))
        found_ids = [row[0] for row in cursor.fetchall()]
        missing_ids = sorted(set(fab_ids) - set(found_ids))
        if missing_ids:
            raise ValueError(f"CSV FABs missing from database; no changes applied: {missing_ids}")
        cursor.execute("SELECT id FROM public.shop_cut_plans WHERE fab_id = ANY(%s) ORDER BY id", (fab_ids,))
        plan_ids = [row[0] for row in cursor.fetchall()]
        cursor.execute(
            "SELECT id FROM public.shop_cut_plan_timer_sessions WHERE shop_cut_plan_id = ANY(%s)",
            (plan_ids,),
        )
        session_ids = [row[0] for row in cursor.fetchall()]
        cursor.execute(
            "SELECT count(*) FROM public.shop_cut_plan_timer_events "
            "WHERE shop_cut_plan_id = ANY(%s) OR session_id = ANY(%s)",
            (plan_ids, session_ids),
        )
        event_count = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM public.files WHERE task_id = ANY(%s)", (plan_ids,))
        file_count = cursor.fetchone()[0]
        cursor.execute(
            "SELECT count(*) FROM public.fabs WHERE id = ANY(%s) AND shop_est_completion_date IS NOT NULL",
            (fab_ids,),
        )
        estimate_count = cursor.fetchone()[0]
        print(f"Matched FABs: {len(found_ids)}; shop plans: {len(plan_ids)}; estimates to clear: {estimate_count}")
        print(f"Dependent timer sessions: {len(session_ids)}; events: {event_count}; linked files: {file_count}")
        if not apply:
            return
        if (session_ids or event_count) and not delete_timer_history:
            raise ValueError("Timer history exists. Review it before explicitly allowing --delete-timer-history.")
        if file_count and not detach_files:
            raise ValueError("Linked files exist. Review them before explicitly allowing --detach-files.")
        if delete_timer_history:
            cursor.execute(
                "DELETE FROM public.shop_cut_plan_timer_events "
                "WHERE shop_cut_plan_id = ANY(%s) OR session_id = ANY(%s)",
                (plan_ids, session_ids),
            )
            cursor.execute("DELETE FROM public.shop_cut_plan_timer_sessions WHERE id = ANY(%s)", (session_ids,))
        if detach_files:
            cursor.execute("UPDATE public.files SET task_id = NULL WHERE task_id = ANY(%s)", (plan_ids,))
        cursor.execute("DELETE FROM public.shop_cut_plans WHERE id = ANY(%s)", (plan_ids,))
        print(f"Deleted shop plans: {cursor.rowcount}")
        cursor.execute(
            "UPDATE public.fabs SET shop_est_completion_date = NULL "
            "WHERE id = ANY(%s) AND shop_est_completion_date IS NOT NULL",
            (fab_ids,),
        )
        print(f"Cleared shop estimates: {cursor.rowcount}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--expected-database", default="alpha_granite_production")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--delete-timer-history", action="store_true")
    parser.add_argument("--detach-files", action="store_true")
    args = parser.parse_args()
    load_dotenv()
    try:
        fab_ids = read_target_fab_ids(args.csv)
        print(f"CSV FABs with pre_shop_review_completed=false: {len(fab_ids)}")
        print(f"FAB IDs: {fab_ids}")
        if not fab_ids:
            print("Nothing to change.")
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
            cleanup(connection, fab_ids, apply=args.apply,
                    delete_timer_history=args.delete_timer_history, detach_files=args.detach_files)
        print("Changes committed." if args.apply else "Read-only preview. Run with --apply after reviewing and backing up.")
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"Error: {error}\n")
    except psycopg2.Error as error:
        parser.exit(1, f"Database operation failed; row changes rolled back. SQLSTATE: {error.pgcode or 'unavailable'}\n")


if __name__ == "__main__":
    main()