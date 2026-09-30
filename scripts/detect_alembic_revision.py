"""
Work out which alembic revision a database's schema actually matches, and
optionally stamp it there.

Use this when alembic_version holds a revision that no longer exists in
alembic/versions (e.g. from migrations removed in commit 293c855), which makes
every alembic command fail. Each revision in the current chain is identified
by a table/column it creates; the latest revision whose changes (and all
earlier ones) are present is the one to stamp.

    python scripts/detect_alembic_revision.py            # report only
    python scripts/detect_alembic_revision.py --stamp    # also rewrite alembic_version
    alembic upgrade head                                 # then apply the rest
"""
import argparse
import os
import sys

import psycopg2
from dotenv import load_dotenv


def column(table, col):
    return ("SELECT EXISTS (SELECT 1 FROM information_schema.columns"
            f" WHERE table_schema='public' AND table_name='{table}' AND column_name='{col}')")


def table(name):
    return ("SELECT EXISTS (SELECT 1 FROM information_schema.tables"
            f" WHERE table_schema='public' AND table_name='{name}')")


def index(name):
    return f"SELECT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='{name}')"


# (revision, check that its changes are present), oldest first.
CHAIN = [
    ("b527e06fbd20", "SELECT true"),
    ("20260701_130000", column("audit_trails", "operation")),
    ("20260804_120000", table("slab_smith_sessions")),
    ("20260804_130000", table("hcp_payroll_source_configs")),
    ("20260806_173000", index("ix_revisions_fab_id")),
    ("20260811_120000", column("slab_smith_session_notes", "sqft_completed")),
    ("20260826_add_miter", column("fabs", "saw_miter_lnft")),
    ("20260831_120000", column("shop_cut_plans", "scheduled_end_date")),
    ("20260901_120000", column("slab_smith_session_notes", "work_percentage_done")),
    ("20260903_120000", column("install_completions", "is_confirmed")),
    ("20260903_130000", column("shop_revisions", "shop_revision_type")),
    ("20260903_140000", "SELECT EXISTS (SELECT 1 FROM information_schema.columns"
                        " WHERE table_schema='public' AND table_name='install_completions'"
                        " AND column_name='completion_date' AND is_nullable='YES')"),
    ("20260904_120000", column("work_stations", "attendance_required")),
    ("20260922_120000", table("hcp_staff_roster_snapshots")),
    # 20260922_130000 only uses IF [NOT] EXISTS, so re-running it is harmless:
    # treat it as applied when its payroll index exists.
    ("20260922_130000", index("ix_hcp_payroll_source_configs_payroll_settings_id")),
    ("20260925_090000", column("hcp_payroll_report_rows", "employee_id")),
    ("20260925_120000", column("hcp_staff_roster_snapshots", "period_start")),
    ("20260930_120000", column("fabs", "is_migrated")),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stamp", action="store_true", help="Rewrite alembic_version to the detected revision")
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
    cur.execute("SELECT version_num FROM alembic_version")
    print("alembic_version now:", ", ".join(r[0] for r in cur.fetchall()) or "(empty)")

    present = []
    for rev, check in CHAIN:
        cur.execute(check)
        present.append((rev, cur.fetchone()[0]))
    for rev, ok in present:
        print(f"  {'applied ' if ok else 'missing '} {rev}")

    detected = None
    for rev, ok in present:
        if not ok:
            break
        detected = rev
    gaps = [rev for rev, ok in present[present.index((detected, True)) + 1:] if ok]
    if gaps:
        sys.exit(f"\nSchema has changes from {', '.join(gaps)} but not everything before them;"
                 " resolve by hand before stamping.")

    print(f"\nSchema matches revision: {detected}")
    if not args.stamp:
        print("Re-run with --stamp to set alembic_version, then run: alembic upgrade head")
        return
    cur.execute("DELETE FROM alembic_version")
    cur.execute("INSERT INTO alembic_version (version_num) VALUES (%s)", (detected,))
    conn.commit()
    print(f"alembic_version set to {detected}. Now run: alembic upgrade head")


if __name__ == "__main__":
    main()
