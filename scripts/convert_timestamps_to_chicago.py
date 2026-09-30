"""
One-off conversion of stored timestamps to America/Chicago wall-clock time.

Every `timestamp without time zone` column is stored in the Postgres session
timezone at the moment the row was written. Before the switch to Chicago the
app wrote rows in another frame (UTC on the servers), so those rows must be
shifted; rows written after the database timezone was changed are already
Chicago time and must be left alone.

Rows are classified per table using when they were written:
  - last write  = COALESCE(updated_at, created_at)
  - first write = COALESCE(created_at, updated_at)
  (the *_timer_events tables use their single event_at column)

  convert : last write is before the cutover  -> every timestamp in the row is in --from-tz
  keep    : first write is at/after the cutover -> already Chicago time
  review  : written/touched around or after the cutover; may hold both frames.
            Left unchanged unless --convert-review-rows is passed.

Because Chicago time runs 5-6 hours behind UTC, a Chicago value written just
after the cutover can look like a UTC value written just before it. Rows whose
marker falls in that window are put in "review" rather than guessed.

Values stored at exactly 00:00:00 are date-only values (e.g. an install date
saved as midnight) and are never shifted, so they stay on the same day.

Usage (dry run is the default; nothing is written without --apply):
    python scripts/convert_timestamps_to_chicago.py --from-tz UTC --cutover "2026-09-30 14:00"
    python scripts/convert_timestamps_to_chicago.py --from-tz UTC --cutover "2026-09-30 14:00" --apply

    # Database that never had its timezone changed (everything is in --from-tz):
    python scripts/convert_timestamps_to_chicago.py --from-tz UTC --all --apply

--cutover is the moment the Postgres timezone was switched, written as
wall-clock time in --from-tz (e.g. UTC). Take a backup (pg_dump) and stop the
web/celery containers before running with --apply.
"""
import argparse
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

TARGET_TZ = "America/Chicago"
MARKER_SETTING = "app.timestamps_converted_to"
SAMPLE_IDS = 15


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--from-tz", required=True, help="Timezone the existing rows were written in (e.g. UTC)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--cutover", help='When the DB timezone was switched, in --from-tz wall-clock, "YYYY-MM-DD HH:MM[:SS]"')
    group.add_argument("--all", action="store_true", help="Convert every row (no rows were written in Chicago time yet)")
    parser.add_argument("--convert-review-rows", action="store_true", help="Also convert rows classified as review")
    parser.add_argument("--apply", action="store_true", help="Commit the changes (default is a dry run)")
    parser.add_argument("--force", action="store_true", help="Run even if this database is already marked as converted")
    return parser.parse_args()


def ambiguity_window(from_tz: str, cutover: datetime):
    """Width of the window in which a Chicago value can look like a --from-tz value."""
    src = cutover.replace(tzinfo=ZoneInfo(from_tz))
    return abs(src.utcoffset() - src.astimezone(ZoneInfo(TARGET_TZ)).utcoffset())


def timestamp_columns(cur):
    cur.execute(
        """
        SELECT c.table_name, array_agg(c.column_name::text ORDER BY c.ordinal_position)
        FROM information_schema.columns c
        JOIN information_schema.tables t
          ON t.table_schema = c.table_schema AND t.table_name = c.table_name AND t.table_type = 'BASE TABLE'
        WHERE c.table_schema = 'public' AND c.data_type = 'timestamp without time zone'
        GROUP BY c.table_name
        ORDER BY c.table_name
        """
    )
    return cur.fetchall()


def table_has_column(cur, table, column):
    cur.execute(
        "SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = %s AND column_name = %s",
        (table, column),
    )
    return cur.fetchone() is not None


def write_markers(columns):
    """SQL expressions for (last write, first write) of a row, or None if unknown."""
    names = set(columns)
    if "created_at" in names or "updated_at" in names:
        present = [sql.Identifier(c) for c in ("updated_at", "created_at") if c in names]
        last = sql.SQL("COALESCE({})").format(sql.SQL(", ").join(present))
        first = sql.SQL("COALESCE({})").format(sql.SQL(", ").join(reversed(present)))
        return last, first
    if len(columns) == 1:
        only = sql.Identifier(columns[0])
        return only, only
    return None


def classification(columns, convert_all):
    """SQL predicates (convert, keep); rows matching neither are review rows."""
    if convert_all:
        return sql.SQL("TRUE"), sql.SQL("FALSE")
    markers = write_markers(columns)
    if markers is None:
        return sql.SQL("FALSE"), sql.SQL("FALSE")
    last, first = markers
    return sql.SQL("{} < %(convert_before)s").format(last), sql.SQL("{} >= %(keep_from)s").format(first)


def converted_value(column):
    col = sql.Identifier(column)
    return sql.SQL(
        "CASE WHEN {col}::time = '00:00:00' THEN {col} "
        "ELSE ({col} AT TIME ZONE %(src)s) AT TIME ZONE %(dst)s END"
    ).format(col=col)


def main():
    args = parse_args()
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL not set in environment or .env")
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")

    ZoneInfo(args.from_tz)  # validate
    cutover = datetime.fromisoformat(args.cutover) if args.cutover else None
    window = ambiguity_window(args.from_tz, cutover) if cutover else None
    if cutover and not window:
        raise SystemExit(f"{args.from_tz} has the same offset as {TARGET_TZ} at the cutover; nothing to convert.")

    conn = psycopg2.connect(database_url)
    conn.autocommit = False
    cur = conn.cursor()
    cur.execute("SET LOCAL lock_timeout = '10s'")

    cur.execute("SELECT current_database(), current_setting('TimeZone')")
    db_name, session_tz = cur.fetchone()
    cur.execute(
        """
        SELECT s FROM pg_db_role_setting d, unnest(d.setconfig) s
        WHERE d.setdatabase = (SELECT oid FROM pg_database WHERE datname = current_database())
          AND d.setrole = 0
        """
    )
    db_settings = dict(s.split("=", 1) for (s,) in cur.fetchall())
    print(f"Database: {db_name}   configured timezone: {db_settings.get('TimeZone', '(server default) ' + session_tz)}")
    print(f"Converting: {args.from_tz} -> {TARGET_TZ}   "
          + (f"cutover: {cutover} {args.from_tz} (review window {window})" if cutover else "all rows")
          + ("" if args.apply else "   [DRY RUN]"))

    already = db_settings.get(MARKER_SETTING)
    if already and not args.force:
        raise SystemExit(f"Database is already marked as converted ({MARKER_SETTING}={already}). Use --force to run again.")

    params = {
        "src": args.from_tz,
        "dst": TARGET_TZ,
        "convert_before": cutover - window if cutover else None,
        "keep_from": cutover,
        "limit": SAMPLE_IDS,
    }
    totals = {"convert": 0, "keep": 0, "review": 0}
    review_tables = []

    for table, columns in timestamp_columns(cur):
        convert_sql, keep_sql = classification(columns, args.all)
        tbl = sql.Identifier(table)
        cur.execute(
            sql.SQL("SELECT count(*) FILTER (WHERE {c}), count(*) FILTER (WHERE {k}), count(*) FROM {t}").format(
                c=convert_sql, k=keep_sql, t=tbl
            ),
            params,
        )
        n_convert, n_keep, n_total = cur.fetchone()
        n_review = n_total - n_convert - n_keep
        totals["convert"] += n_convert
        totals["keep"] += n_keep
        totals["review"] += n_review
        if n_total == 0:
            continue

        midnight = sql.SQL(", ").join(
            sql.SQL("count(*) FILTER (WHERE {c}::time = '00:00:00')").format(c=sql.Identifier(c)) for c in columns
        )
        cur.execute(sql.SQL("SELECT {m} FROM {t} WHERE {c}").format(m=midnight, t=tbl, c=convert_sql), params)
        skipped = [f"{c}={n}" for c, n in zip(columns, cur.fetchone()) if n]
        print(f"  {table:45s} convert={n_convert:<7} keep={n_keep:<7} review={n_review:<7}"
              + (f" date-only kept: {', '.join(skipped)}" if skipped else ""))

        if n_review:
            id_col = sql.Identifier("id") if table_has_column(cur, table, "id") else sql.SQL("ctid")
            cur.execute(
                sql.SQL("SELECT {i}::text FROM {t} WHERE NOT ({c}) AND NOT ({k}) ORDER BY {i} LIMIT %(limit)s").format(
                    i=id_col, t=tbl, c=convert_sql, k=keep_sql
                ),
                params,
            )
            review_tables.append((table, n_review, [r[0] for r in cur.fetchall()]))

        where = sql.SQL("NOT ({k})").format(k=keep_sql) if args.convert_review_rows else convert_sql
        assignments = sql.SQL(", ").join(
            sql.SQL("{} = {}").format(sql.Identifier(c), converted_value(c)) for c in columns
        )
        cur.execute(sql.SQL("UPDATE {t} SET {a} WHERE {w}").format(t=tbl, a=assignments, w=where), params)

    print(f"\nTotal rows  convert={totals['convert']}  keep={totals['keep']}  review={totals['review']}")
    if review_tables:
        action = "CONVERTED" if args.convert_review_rows else "left unchanged"
        print(f"\nReview rows ({action}) — written or touched around/after the cutover; check a few by hand:")
        for table, count, ids in review_tables:
            print(f"  {table}: {count} row(s), e.g. ids {', '.join(ids)}")

    if not args.apply:
        conn.rollback()
        print("\nDry run only: rolled back. Re-run with --apply to commit.")
        return

    cur.execute(
        sql.SQL("ALTER DATABASE {} SET {} = {}").format(
            sql.Identifier(db_name),
            sql.SQL(MARKER_SETTING),
            sql.Literal(f"{TARGET_TZ} from {args.from_tz} at {datetime.now(ZoneInfo(TARGET_TZ)).isoformat(timespec='seconds')}"),
        )
    )
    conn.commit()
    print("\nCommitted.")


if __name__ == "__main__":
    try:
        main()
    except psycopg2.Error as exc:
        print(f"Database error, nothing committed: {exc}", file=sys.stderr)
        sys.exit(1)
