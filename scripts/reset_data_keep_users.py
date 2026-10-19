"""
Wipe all business data, keeping logins, access control and configuration.

Kept: users and what login/permissions need (roles, user_roles, permissions,
role_permissions, action_menus, departments, status), shop/app configuration
(planning_sections, work_stations, service_level_settings,
hcp_payroll_source_configs) and alembic_version. Every other table in the public
schema is emptied with TRUNCATE ... RESTART IDENTITY (no CASCADE, so a foreign
key from a kept table to a wiped one aborts the whole thing instead of silently
wiping more). The schema itself is untouched.

    python scripts/reset_data_keep_users.py                          # preview
    python scripts/reset_data_keep_users.py --apply --confirm-db NAME

Take a pg_dump first. Intended for dev/demo databases before a fresh import.
"""
import argparse
import os
import sys

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

KEEP = {
    "users", "roles", "user_roles", "permissions", "role_permissions", "action_menus",
    "departments", "status",
    "planning_sections", "work_stations", "service_level_settings", "hcp_payroll_source_configs",
    "alembic_version",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="Actually truncate (default: preview)")
    ap.add_argument("--confirm-db", help="Name of the database being wiped; required with --apply")
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
    cur.execute("SELECT current_database()")
    db_name = cur.fetchone()[0]
    cur.execute("SELECT table_name FROM information_schema.tables"
                " WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY 1")
    tables = [r[0] for r in cur.fetchall()]
    wipe = [t for t in tables if t not in KEEP]

    def rows(t):
        cur.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(t)))
        return cur.fetchone()[0]

    print(f"Database: {db_name}\n\nKEEP:")
    for t in tables:
        if t in KEEP:
            print(f"  {t:40s} {rows(t):>8}")
    print("\nWIPE:")
    total = 0
    for t in wipe:
        n = rows(t)
        total += n
        print(f"  {t:40s} {n:>8}")
    print(f"\n{len(wipe)} tables, {total} rows to delete.")

    if not args.apply:
        print(f"\nPreview only. To wipe: --apply --confirm-db {db_name}")
        return
    if args.confirm_db != db_name:
        sys.exit(f"\nRefusing: --confirm-db must be exactly '{db_name}'.")

    cur.execute(sql.SQL("TRUNCATE {} RESTART IDENTITY").format(
        sql.SQL(", ").join(sql.Identifier(t) for t in wipe)))
    conn.commit()
    print(f"\nWiped {len(wipe)} tables. Logins, roles and configuration kept.")


if __name__ == "__main__":
    main()
