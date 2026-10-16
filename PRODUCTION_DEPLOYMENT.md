# Production Deployment

Production API: `https://api.odysseytracker.com`.
Frontend: `https://ag.odysseytracker.com`.
This setup shares a Linux host with staging and uses host Nginx for HTTPS.
It does not use the shared `docker-compose.yml` or start Docker Nginx/Certbot.

## Configuration

- Private runtime settings: `.env.production` (gitignored; transfer separately).
- Reusable template: `compose.production.env.example` (contains no credentials).
- Services: `compose.production.yml`; Compose project: `ag_production`.
- API host listener: `127.0.0.1:8003`; confirm that port is free on the server.
- Static storage: `/var/www/production/backend/alphagranite-backend/static`.
  Change `STATIC_HOST_DIR` if the production storage location differs. Never
  point it at staging storage. Redis and log volumes are project-scoped.
- CORS allows only `https://ag.odysseytracker.com`, not staging or localhost.
- Monthly reports start disabled. Verify mail, imported data, and recipients
  before setting `EOM_STATUS_REPORT_ENABLED=true` and recreating the API.

The prepared local `.env.production` contains the supplied production database
connection, the supplied mail configuration, and separate random JWT/admin
secrets. Rotate the database and mail passwords shared in chat before go-live;
update the relevant env files and recreate affected services. Retrieve the admin
password directly from the private env file, not a terminal transcript.
`SUPERUSER_*` variables do not create a user automatically.

Keep the env file mode at `600`. Do not commit it, source it as shell code, run
plain `docker compose config` in shared logs, or print it in deployment output.
Use `config --quiet`. `.dockerignore` excludes env files and Certbot storage.
TLS certificate paths belong to host Nginx, not the application env.

## Server Preparation

Use a dedicated production checkout with Docker Engine and Compose installed.
Transfer the private env file securely; git will not transfer it. Do not reuse
staging's env file, JWT secret, database, checkout, or upload directory.

From the production checkout, define this shell helper:

```bash
dc() {
  docker compose --env-file .env.production -f compose.production.yml -p ag_production "$@"
}
chmod 600 .env.production
dc config --quiet
dc build
```

Before starting services, create the directory named by `STATIC_HOST_DIR` with
your deployment account. If that needs elevated privileges, an administrator
must create it. Initialize ownership inside the production-only mounts:

```bash
dc run --rm --no-deps --user root web sh -c 'mkdir -p /app/static/uploads /app/static/defaults /app/static/jobs /app/logs && chown -R appuser:appuser /app/static /app/logs'
```

The server/containers must be able to reach `192.168.1.98:5432`. PostgreSQL must
allow the production role from the container host's network address, and that
role must own the production database or have schema creation privileges. Do
not grant access to the staging database. An administrator can check the
production database ownership and grant `USAGE, CREATE ON SCHEMA public` inside
`alpha_granite_production` if needed. Use SCRAM authentication and restrict
network access; do not expose PostgreSQL publicly. Use verified PostgreSQL TLS
if the database server provides it.

## New Empty Database Only

The Alembic baseline is a no-op and does not create application tables.
`alembic upgrade head` is therefore not a fresh-database installer.
The following commands are only for the newly created, empty production DB.
The first command checks emptiness and database connectivity without printing
the connection string:

```bash
dc run --rm --no-deps web python -c 'import os; from sqlalchemy import create_engine, inspect; engine = create_engine(os.environ["DATABASE_URL"]); assert not inspect(engine).get_table_names(), "Database is not empty: stop and use the existing-database instructions"; print("Empty database confirmed")'
dc run --rm --no-deps web alembic stamp base
dc run --rm --no-deps web python scripts/sync_schema_to_models.py
```

Review the preview before applying. It should propose creating the model schema
in the empty database. Stop on unexpected errors or proposed differences.
Then create the schema and stamp the current head:

```bash
dc run --rm --no-deps web python scripts/sync_schema_to_models.py --apply
dc run --rm --no-deps web alembic current
dc run --rm --no-deps web alembic check
```

This uses the current models, not historical data migrations. It is not a way
to upgrade a populated database. Do not use `scripts/auto_migrate.py`, which
can drop tables, or run `seed_all.py` blindly in production.

Load only required reference data and the initial administrator:

```bash
dc run --rm --no-deps web python scripts/load_default_status.py
dc run --rm --no-deps web python scripts/load_default_action_menu.py
dc run --rm --no-deps web python scripts/load_default_departments.py
dc run --rm --no-deps web python scripts/load_default_roles.py
dc run --rm --no-deps web python scripts/create_superuser.py
```

Accounts, employees, stones, planning sections, workstations, and operational
data need an approved production import or configuration. The commands above
do not populate those. Confirm the intended admin identity in the env before
running the bootstrap; change its password after the first login.

## Existing Database Updates

Back up the production database and uploads before schema changes. Check the
current revision, take production services down for a maintenance window, and
apply reviewed migrations with the new image. No staging services are touched:

```bash
dc run --rm --no-deps web alembic current
dc stop web celery_worker celery_beat
dc run --rm --no-deps web alembic upgrade head
```

If the database is unversioned or at an unknown revision, stop and reconcile its
schema/history first. Never stamp a populated database simply to suppress an
upgrade error. Failed migrations must be resolved before starting services.

## Start and Verify

After database setup or successful migrations:

```bash
bash deploy-stack.sh production
dc ps
curl --fail http://127.0.0.1:8003/health/
dc logs --tail=100 web celery_worker celery_beat
```

`deploy-stack.sh` validates configuration and starts services; it does not
initialize the database, run migrations, or create an administrator. The
dedicated Compose file ignores the old migration entrypoint intentionally.
One API process owns the monthly-report scheduler; run exactly one Celery beat
instance. Celery owns HCP scheduling, so the in-API HCP scheduler is disabled.
Review/import HCP source settings before enabling scheduled data ingestion.

The HTTP health check is liveness only. Verify a real authenticated database
request and the FAB list, login/refresh, file upload/download, and Celery jobs
after configuration/import. Test SMTP delivery separately before enabling
monthly reports. A healthy container does not prove the schema or mail works.

## Host Nginx and HTTPS

Point the API DNS record at the existing reverse-proxy host. Use
`nginx/production.host.conf.example` as a separate host Nginx site; do not
replace the staging site. It forwards only the API domain to port `8003`.
The frontend domain requires its own frontend deployment/site.

An administrator should install and enable that API site, validate with
`nginx -t`, and reload Nginx. Then issue/install a certificate for the API
domain using the host's existing certificate workflow. For host Certbot with
the Nginx plugin, after DNS and port 80 reach this host:

```bash
sudo certbot --nginx -d api.odysseytracker.com --redirect
sudo nginx -t
sudo systemctl reload nginx
sudo certbot renew --dry-run
```

Run elevated commands directly on the server. Keep the API loopback-only;
public access should use Nginx on ports 80/443. Do not open port `8003` in the
firewall. Confirm TLS, the public health URL, frontend CORS, and staging health:

```bash
curl --fail https://api.odysseytracker.com/health/
curl --fail -i -X OPTIONS https://api.odysseytracker.com/api/v1/fabs \
  -H 'Origin: https://ag.odysseytracker.com' \
  -H 'Access-Control-Request-Method: GET'
curl --fail https://api.staging.odysseytracker.com/health/
```

Expected CORS origin: `https://ag.odysseytracker.com`. Ensure PostgreSQL and
production static storage have scheduled, tested backups before go-live.
Do not use `docker compose down -v`: it removes persistent project volumes.