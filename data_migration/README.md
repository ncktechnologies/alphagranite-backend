# Caspio Migration Runbook

The migration follows `plan-legacyXmlMigration.prompt.md` and loads the CSV exports in phases:

1. Reference data, accounts, jobs, and fabs.
2. Stage rows, notes, costs, revisions, and files.
3. Drafting, final-programming, and shop timer history.

Employee and machine assignments are intentionally deferred. Unresolved values are recorded in `unresolved_references`; source rows that cannot be linked to a `Fab_Status` record are recorded in `migration_rejects`.

## Local Docker Run

The web container must use the local static directory on macOS:

```sh
STATIC_HOST_DIR=./static docker compose --env-file .env up -d --build web
```

Preview the import without committing data:

```sh
docker compose --env-file .env exec -T web \
  python data_migration/migrate.py \
  --input data_migration/actual_caspio_data_csv \
  --dry-run
```

Create a PostgreSQL backup with the host `pg_dump` client matching the server version, then run the import:

```sh
set -a; . ./.env; set +a
pg_dump "$DATABASE_URL" > /tmp/alphagranite-before-caspio.sql

docker compose --env-file .env exec -T web \
  python data_migration/migrate.py \
  --input data_migration/actual_caspio_data_csv
```

The importer uses `DATABASE_URL`, converts SQLAlchemy URLs for psycopg2, and resolves `localhost` to `host.docker.internal` inside Docker. It is safe to rerun; natural keys and legacy FAB IDs prevent duplicate growth.

## Reconciliation

After the import, inspect the command reconciliation output and these tables:

```sql
SELECT source_table, count(*) FROM migration_rejects GROUP BY source_table;
SELECT kind, count(*) FROM unresolved_references GROUP BY kind ORDER BY count(*) DESC;
```

The current export produced 9,947 imported fabs, 3,208 new business jobs, 1,245 new accounts, 29,937 operator timer sessions/events, 31 unique rejects, and 180,014 deferred reference records. The rejected rows are orphaned history/revision records whose FAB IDs are absent from `Fab_Status` and must be reviewed before production cutover.