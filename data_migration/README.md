# Caspio Migration Runbook

The migration follows `plan-legacyXmlMigration.prompt.md` and loads the CSV exports in phases:

1. Reference data, accounts, jobs, and fabs.
2. Stage rows, notes, costs, revisions, and files.
3. Drafting, final-programming, and shop timer history.

Imported FABs are flagged `fabs.is_migrated = true` with `fabs.migration_source = 'caspio'` (alembic revision `20260930_120000`); FABs created in Odyssey stay `false`. Every other imported row is linked to one of those FABs and is written by the `migration_bot` user.

Mapping rules worth knowing:

- Caspio checkboxes export as `-1` (checked) / `0` (unchecked).
- Imported decimal measurements and money values are rounded to 2 decimal places; integer and duration conversions retain their existing behavior.
- Cost of stone is stored in `fabs.cost_of_stone`; the importer does not create `cost_of_stones` rows or set `fabs.cost_of_stone_id`.
- The Fab_Status **Complete** checkbox means install complete. Those FABs get `current_stage = 'install_completion'`, `next_stage = NULL` and stay Active (status 1), the same as FABs completed in the app. They also get a completed `install_schedulings` row and a completed `install_completions` row, and their shop plans are set to 100%, so they match the app's `install_status=complete` filter.
- Incomplete FABs are placed on the Odyssey stage matching their Caspio flags (templating, pre_draft_review, … cut_list, install_scheduling, install_completion). No `install_completions` row is created for them, so installers can complete them in the app.
- Caspio `install_date` is the install date. Caspio `completion_date` is the shop completion date: it is used only when `install_date` is blank, and the raw value is kept in `fabs.notes`.
- Dates are stored as America/Chicago wall-clock, exactly as shown in Caspio.

Employees are linked to Odyssey users by `data_migration/employees.py`:

- Caspio clock numbers (`Shop_Data.shop_employee`, `Fab_Status.cut_by/edging_by/miter_by/cnc_by/qc_by/wj_by/resurface_by`) are matched to `users.hcp_employee_id`. A match is used only when the names agree too, because some clock numbers were reused. For example, Caspio 532 is Fernando Valencia-Lujano, while HCP 532 is Antonio Garcia.
- Where the ID match fails, a person is matched by first and last name, using the name from `Employees_Shop`, `Alpha_Employees` or `ProductionPerPerson`. The `*_employee_scheduled` columns hold names and are matched the same way.
- `template_by` uses `Employees_Template`; `sct_by` and `revision_info.SalesPerson` use `Active_Sales_Employees`. These lists hold only first names, which are resolved through `Alpha_Employees` (e.g. Gabe → Gabe Poulos → clock 155). Failing that, the name must be the only Odyssey user with that first name.
- Linked fields: `fabs.sales_person_id`, `templatings.technician_id`, `sales_cts.drafter_id`, `shop_cut_plans.user_id`, `wj_schedulings.technician_id`, `resurface_schedulings.technician_id`, and `operator_job_timer_sessions/events.operator_id`. Anything that can't be linked keeps `migration_bot` (or NULL) and is logged in `unresolved_references` (kind `employee`).
- Not linked: `draft_by`, `final_by`, `installer`, `Draft_Data.drafter`, `FP_Data.programmer` and `revision_info.Revisor`. Their ID list (the office/drafter employee table) is not in the export.

Add `--employee-report unlinked.csv` to list every Caspio person that could not be linked. Clock-number conflicts are printed in the reconciliation output.

Machine assignments are intentionally deferred. Unresolved values are recorded in `unresolved_references`; source rows that cannot be linked to a `Fab_Status` record are recorded in `migration_rejects`.

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

Create a PostgreSQL backup with the host `pg_dump` client matching the server version. Then apply the alembic migrations (for the `is_migrated` column) and run the import.

If this database already holds an import made by an older version of this script, which stored UTC times, run `scripts/convert_timestamps_to_chicago.py` **before** re-running the import. Otherwise the re-run cannot match earlier timer sessions by start time, and will add duplicates.

```sh
set -a; . ./.env; set +a
pg_dump "$DATABASE_URL" > /tmp/alphagranite-before-caspio.sql

docker compose --env-file .env exec -T web \
  python data_migration/migrate.py \
  --input data_migration/actual_caspio_data_csv
```

The importer uses `DATABASE_URL`, converts SQLAlchemy URLs for psycopg2, and resolves `localhost` to `host.docker.internal` inside Docker. It is safe to rerun; natural keys and legacy FAB IDs prevent duplicate growth.

## Production Docker Run

Use the dedicated production Compose file and project, not just
`--env-file .env.production`. The env file alone does not select a Compose file.
Complete the schema/bootstrap steps in
[PRODUCTION_DEPLOYMENT.md](../PRODUCTION_DEPLOYMENT.md) and take a verified
production database backup before importing. Keep application/background writes
paused for the import, and review the reconciliation before reopening access.

Transfer the complete `actual_caspio_data_csv` export folder to
`data_migration/actual_caspio_data_csv` in the production checkout if it is not
already there. Use the approved current export, not just one CSV file. The
commands below mount it read-only, so it does not need to be baked into the
image and updates to the CSVs do not require another image build.

From `/var/www/production/backend/alphagranite-backend`, after transferring the
updated importer code:

```sh
dc() {
  docker compose --env-file .env.production -f compose.production.yml -p ag_production "$@"
}
dc build web
dc stop web celery_worker celery_beat
test -d "$PWD/data_migration/actual_caspio_data_csv" || { echo "CSV folder missing"; exit 1; }
dc run --rm --no-deps -T \
  -v "$PWD/data_migration/actual_caspio_data_csv:/migration-csv:ro" \
  web python -c 'from pathlib import Path; files = list(Path("/migration-csv").glob("*.csv")); assert files, "No CSV files found"; assert any(path.name.startswith("Fab_Status") for path in files), "Fab_Status export missing"; print("CSV export mounted:", len(files), "files")'
dc run --rm --no-deps -T \
  -v "$PWD/data_migration/actual_caspio_data_csv:/migration-csv:ro" \
  web python data_migration/migrate.py --input /migration-csv --dry-run
```

`--dry-run` rolls back table writes, but PostgreSQL sequence changes are not
transactional: ID counters can advance during the preview. It is not a
read-only database operation. Use a cloned database if a completely untouched
production database is required for the preview.

After reviewing the preview and confirming the backup, apply the import:

```sh
dc run --rm --no-deps -T \
  -v "$PWD/data_migration/actual_caspio_data_csv:/migration-csv:ro" \
  web python data_migration/migrate.py --input /migration-csv
```

Review rejects, unresolved employee links, and actual imported totals. Restart
production only after successful verification:

```sh
dc up -d web celery_worker celery_beat
```

### Duplicate User ID During Import

`users_pkey: Key (id)=(1) already exists` while creating `migration_bot` is
consistent with a users ID sequence behind existing rows, not duplicate CSV
rows. The importer repairs serial sequences before creating that user. Older
code only repaired a sequence when `max(id) > last_value`, missing the case
where both are `1` but the sequence has not been called yet. Update the
importer and rebuild the production image before retrying; the repair now
handles equality without lowering a sequence that is already ahead.
Do not delete the existing user or reset its ID to work around the error.

## Reconciliation

After the import, inspect the command reconciliation output and these tables:

```sql
SELECT source_table, count(*) FROM migration_rejects GROUP BY source_table;
SELECT kind, count(*) FROM unresolved_references GROUP BY kind ORDER BY count(*) DESC;
```

The current export produced 9,947 imported fabs, 3,208 new business jobs, 1,245 new accounts, 29,937 operator timer sessions/events, 31 unique rejects, and 180,014 deferred reference records. The rejected rows are orphaned history/revision records whose FAB IDs are absent from `Fab_Status` and must be reviewed before production cutover.