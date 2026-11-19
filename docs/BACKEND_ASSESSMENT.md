# Odyssey Tracker Backend: Assessment and Implementation Plan

Assessed 2026-11-17 against branch `production` (commit `9199711`). Scope: `src/app`, `alembic`, `tests`, Docker/nginx/CI files and the tracked scripts and data in the repository root.

The companion documents are `WEB_ASSESSMENT.md` (web repo, `docs/`), `INSTALLER_APP_ASSESSMENT.md` (installer app repo, `docs/`) and `ODYSSEY_MOBILE_APP_PLAN.md` (this folder).

## 1. Summary

The backend is a FastAPI + SQLModel + PostgreSQL service of about 56,000 lines with 55 router modules, Celery for payroll ingestion, and an AI/MCP reporting layer. The workflow logic is rich and the newer code (batched loaders in `routers/fabs.py`, the guarded SQL tool, the timer guards, the audit trail) is carefully written.

The main risk is access control. Seven findings, taken together, mean that anyone with a login can read and change almost everything, and that someone without a login can take over an account:

| # | Finding | Effect |
|---|---|---|
| BE-SEC-01 | Access tokens are issued without an expiry | A leaked token works forever |
| BE-SEC-02 | Password-reset code can be brute-forced | Takeover of any account, including the super admin |
| BE-SEC-03 | Uploaded files are served without authentication by sequential ID | Anyone on the internet can download every drawing, photo and document |
| BE-SEC-04 | Most business endpoints check only that the caller is logged in | Any employee can read owner reports, labour cost and payroll-derived data, and change rates, stages and FABs |
| BE-SEC-05 | Request bodies are logged in full | Plaintext passwords and reset codes are in the log files |
| BE-SEC-06 | Real user passwords and an admin password are committed to git | Credentials are readable by anyone with repo access |
| BE-SEC-07 | Refresh tokens and reset tokens are accepted as access tokens | Token-type separation does not exist |

Fix Phase 0 before any other work in this document. Each item has an ID, the files involved, the change to make and a way to confirm it.

Severity: **Critical** = exploitable now with serious impact; **High** = fix this sprint; **Medium** = fix this quarter; **Low** = tidy-up.
Effort: **S** = under half a day, **M** = 1–2 days, **L** = 3–5 days, **XL** = more than a week.

## 2. Phase 0: fix immediately

### BE-SEC-01. Access tokens never expire (Critical, S)

`AuthService.create_access_token` in `src/app/service/auth.py:63` sets `iat` and `type` but never sets `exp`. The `expires_delta` argument and `ACCESS_TOKEN_EXPIRE_MINUTES` are ignored. PyJWT only rejects an expired token when `exp` is present, so every access token ever issued is still valid.

The only time limit is the 8-hour inactivity check in `middleware/jwt_auth.py:get_current_user`, which has three gaps: it applies only to routes that use that dependency, it reads `users.updated_at` (which any profile edit or admin update resets), and one active device keeps every other token for that user alive.

Change:
1. Set `exp = now + ACCESS_TOKEN_EXPIRE_MINUTES` in `create_access_token`. Use 30–60 minutes, and add `jti`.
2. Decode with `options={"require": ["exp", "iat", "type"]}`.
3. Rotate `SECRET_KEY` in every environment when this ships, so all existing non-expiring tokens die. Everyone logs in once.
4. Web and installer app must refresh on 401 (see BE-BUG-01 for the endpoint mismatch that currently breaks this).

Confirm: a token older than the configured lifetime gets 401; a token signed with the old key gets 401.

### BE-SEC-02. Password reset code can be brute-forced (Critical, S)

`POST /auth/reset-password` in `src/app/routers/auth.py:538` compares the submitted code and returns "Invalid verification code" without incrementing `attempts`. The attempt limit exists only in `AuthService.verify_reset_otp`, and the route that called it is commented out. The code is six digits, valid for ten minutes, and there is no rate limiting. The code is generated with `random.choices`, which is not a cryptographic generator. `POST /auth/request-password-reset` is unauthenticated, so an attacker can start a reset for `admin` and guess codes until one works.

Change:
1. In `reset_password`, call `verify_reset_otp` (which counts attempts and deletes the code after three failures) and delete the duplicated inline check.
2. Generate the code with `secrets.randbelow(10**6)`. Store a hash of it, not the code.
3. Rate-limit `/auth/*` (BE-SEC-08).
4. Revoke the user's existing sessions when a reset completes (BE-SEC-09).

Confirm: the fourth wrong code for a user returns "request a new code", and the right code no longer works after that.

### BE-SEC-03. Files are downloadable without authentication (Critical, M)

`JWTAuthMiddleware` in `src/app/middleware/jwt_auth.py:13-28` skips authentication for:
- `/api/v1/files/{id}/view` and `/files/{id}/view`. File IDs are sequential integers, so a loop from 1 upward downloads everything.
- any path containing `/media/` and ending in `/view`
- `/api/v1/files/download/{filename}`
- `/static...`
- `/api/v1/test-public`, which also returns the server's upload directory path

These are public so that `<img>`, `<iframe>` and PDF viewers can load files without an `Authorization` header. Keep that ability with signed URLs:

1. Add `GET /api/v1/files/{id}/signed-url` (authenticated, permission-checked) that returns `/api/v1/files/{id}/view?exp=<unix>&sig=<hmac>`, where `sig = HMAC-SHA256(FILE_URL_SECRET, f"{id}:{exp}")` and the lifetime is 5–15 minutes.
2. `view` and `download` accept a valid signature or a valid bearer token, and nothing else.
3. Wherever a response includes `file_url` (`FileService._serialize_file`, job media, drafting, CNC, slabsmith, final programming), return a signed URL.
4. Delete `/test-public`, the `download_file` duplicates in `routers/public_files.py` and `routers/job_extras.py:800`, and the dead `/static` skip.
5. Remove the three overlapping "public path" lists: the middleware list, `PUBLIC_PATHS`/`is_public_path`, and the two no-op `@app.middleware("http")` functions in `main.py:133-154`. Keep one allowlist with exact-match or prefix rules.

Confirm: `curl https://api.../api/v1/files/1/view` returns 401; the same URL with a fresh signature returns the file; an expired signature returns 401.

### BE-SEC-04. Most endpoints have no authorisation (Critical, L)

`PermissionChecker` is used in 11 of 55 router modules (accounts, action menu, department, edges, employee, role, stone colours, stone thickness, stone types, MCP, and two routes in jobs). Everything else depends only on `get_current_user`, or on nothing. Examples of what any logged-in employee, including an installer on the tablet app, can call today:

| Endpoint | File |
|---|---|
| All 47 `/reports/...` routes, including weekly labour cost, installer rates and the PDF/XLSX exports | `routers/reports.py` |
| `POST /reports/owner/installer-rates` (set anyone's hourly rate) | `routers/reports.py:8081` |
| `POST /reports/owner/end-of-month-status/send-test?email=...` (email the management report to any address) | `routers/reports.py:8336` |
| `GET /audit-trails` (everyone's activity, IPs and devices) | `routers/audit_trails.py` |
| `PATCH /fabs/{id}/stage` (docstring says "admin-only handled in view"), `DELETE /fabs/{id}`, `PUT /fabs/{id}` | `routers/fabs.py` |
| `DELETE /files/{id}` (delete any file) | `routers/file.py` |
| Templater timers for any `templater_id` passed in the query string | `routers/job_timers.py:741` |
| Create, update and delete planning sections and shop planning with no user dependency at all | `routers/planning_section.py`, `shop_planning.py`, `shop_planning_section.py`, `operator_workflow.py` |

The web hides menu items by permission, but that is presentation only.

Change:
1. Make the secure path the default. Add a router-level dependency so a router cannot be registered without a declared resource:
   ```python
   router = APIRouter(dependencies=[Depends(require("reports", "read"))])
   ```
   and override per route for write actions.
2. Map every router to an action-menu code. Use the codes the web already sends as `permissionKey` (`jobs`, `shop`, `reports`, `performance`, `account`, `employees`, `department`, `roles_permissions`, `stone_types_colors`, `shop_settings`, `notifications`), plus the stage codes used by `use-job-stage` on the web.
3. Owner financial reports, installer rates, HCP payroll and audit trails need their own codes (`reports_financial`, `audit_trails`). Do not gate them behind the general `reports` code.
4. Replace the ad hoc `is_super_admin` checks in `hcp_payroll.py`, `operators.py` and `shop_cut_plan.py` with the same dependency.
5. Object-level rules: timers must act on `current_user.id` unless the caller holds a supervisor permission (remove `templater_id` from the query string for non-supervisors); installers see only FABs they are scheduled on. `GET /fabs?user_level=installer` currently trusts a client-supplied flag (`routers/fabs.py:1201,1289`); derive it from the user's roles.
6. Add a test that walks `app.routes` and fails if any route outside an explicit public allowlist has no permission dependency. This stops the problem returning.

Confirm: the route-walk test passes; a user with only the installer role gets 403 from `/api/v1/reports/owner/weekly-fabrication-labor-cost`.

### BE-SEC-05. Passwords and reset codes are written to the logs (Critical, S)

`RequestLoggerMiddleware` in `src/app/middleware/request_logger.py` logs the full JSON body of every POST/PUT/PATCH/DELETE. That includes `/auth/login`, `/auth/change-password` and `/auth/reset-password`. Eight log files in the local `applog/` directory contain a `"password"` key, which confirms it. It also reads every upload fully into memory before the route runs.

Change:
1. Stop logging bodies. Log method, path, status, duration, user ID and a request ID on one line.
2. If body logging is needed for debugging, make it opt-in by environment variable, skip `/auth/*` and multipart requests, and redact keys matching `password|otp|token|secret`.
3. Purge or restrict existing log files on every server, and force a password reset for users whose passwords were logged (in practice, everyone).
4. Replace `BaseHTTPMiddleware` with a pure ASGI middleware so request bodies are not buffered.

### BE-SEC-06. Credentials committed to git (Critical, S)

- `create_users.py` and `create_bulk-users.py` contain real staff usernames with plaintext passwords that follow a `Lastname123!` pattern.
- `scripts/reset_admin_password_fresh.py` sets the `admin` password to a hardcoded value.
- `src/app/utils/config.py:64` defaults `SUPERUSER_PASSWORD` to `admin123`.
- `src/app/routers/job_extras.py:41` defaults `BASE_URL` to a raw server IP over HTTP.

Change:
1. Force a password change for every user created by those scripts and for `admin`. Confirm no account still uses the pattern.
2. Delete the scripts, or rewrite them to read from an untracked file and generate random passwords.
3. Remove the defaults; fail at startup if `SECRET_KEY`, `SUPERUSER_PASSWORD` or `DATABASE_URL` is missing or shorter than a minimum length.
4. Purge the files from history with `git filter-repo` once the passwords are rotated. This rewrites history, so agree a time with everyone who has a clone.

### BE-SEC-07. Any signed token is accepted as an access token (Critical, S)

`decode_token` does not check the `type` claim, and the middleware accepts whatever decodes. A 7-day refresh token works as an access token, and so does the JWT from `create_password_reset_token`. The middleware also accepts a raw token with no `Bearer ` prefix.

Change: in the middleware and both `get_current_user` functions, require `type == "access"`. In `/auth/refresh-token`, require `type == "refresh"` (already done). Require the `Bearer` scheme. Delete the unused JWT reset-token functions.

## 3. Phase 1: security hardening

### BE-SEC-08. No rate limiting or lockout (High, M)

Account lockout in `routers/auth.py` is commented out as "TEMPORARILY DISABLED". There is no rate limiting anywhere. Every failed login for an unknown username also emails `ADMIN_EMAIL` (`auth.py:150`), so a script can flood the admin mailbox.

Change: add `slowapi` or an nginx `limit_req` zone for `/auth/*` (for example 10 per minute per IP and 5 per minute per username). Re-enable lockout with a 15-minute automatic unlock. Replace the per-failure email with a daily digest or a threshold alert.

### BE-SEC-09. No session revocation; deactivated users keep access (High, M)

Tokens are stateless and nothing checks `users.status` after login. `routers/auth.py:get_current_user` (used by `PermissionChecker`) checks only that the user row exists. A deactivated or deleted employee keeps working access.

Change:
1. One `get_current_user`, in one module, that checks token type, `status == 1`, and a `token_version` integer on `users` that is also embedded in the token. Increment it on password change, password reset, deactivation and "log out everywhere".
2. Store refresh tokens server-side (hashed, with `jti`, device ID and expiry) and rotate on use, so a stolen refresh token can be detected and revoked.
3. Add `POST /auth/logout`.
4. Track last activity in Redis or a dedicated column. `get_current_user` currently writes `users.updated_at` and commits on every request (`jwt_auth.py:144`), which is one extra write transaction per API call and corrupts the meaning of `updated_at`.

### BE-SEC-10. Unauthenticated account unlock (High, S)

`POST /auth/unlock-account/{user_id}` (`routers/auth.py:650`) has no dependency, and `/auth/*` is skipped by the middleware. Move it under `/api/v1/employees/{id}/unlock` with `require("employees", "update")`. Then narrow the middleware skip from the `/auth/` prefix to the exact public routes: login, refresh-token, request-password-reset, resend-reset-otp and reset-password.

### BE-SEC-11. Stored XSS through notes (High, S)

Note text is stored as entered and the web renders it with `dangerouslySetInnerHTML` (web finding WEB-SEC-01). Combined with tokens in `localStorage`, one malicious note can steal the session of every user who opens that job.

Change: the web must sanitise or stop rendering HTML (primary fix). On the backend, strip tags on write for all note fields with `nh3` and add a `Content-Security-Policy` header at nginx as a second layer.

### BE-SEC-12. Upload handling (High, M)

In `routers/file.py` and `service/file.py`:
- `directory` is a client form field joined into the path with no validation, so `directory=../../somewhere` writes outside the static root. Validate against an allowlist (`uploads`, `jobs`, `profile`).
- The extension check is skipped when the filename has no extension, and the content type is taken from the client. Check the real type from the file's first bytes.
- Files are written with `chmod 0o777`. Use `0o640`.
- The file is read into memory twice. Stream to disk in chunks and enforce the size limit while streaming.
- `/app/static` is hardcoded in four places. Use `settings.STATIC_DIR`.
- `DELETE /files/{id}` has no ownership or permission check.
- `MAX_UPLOAD_SIZE` is 5 MB while nginx allows 100 MB. Decide one limit per file category and apply it in both places.
- Serve user uploads with `Content-Disposition: attachment` and `X-Content-Type-Options: nosniff` unless the type is a known image or PDF.

Longer term, move uploads to object storage (S3 or compatible) with pre-signed URLs. That also removes the shared-volume dependency between `web` and `celery_worker`.

### BE-SEC-13. Secrets stored and returned in plaintext (Medium, M)

- `hcp_payroll_source_configs.client_secret` is stored in plaintext and returned in API responses (`routers/hcp_payroll.py:77`), along with the token response JSON for each run (`:97`). Encrypt at rest (Fernet with a key from the environment), never return the secret, and stop storing token responses.
- New employee passwords are generated with `random` (`service/employee.py:48`), emailed in plaintext and returned in the API response. Use `secrets`, and replace the emailed password with a one-time set-password link.
- The Gemini API key is passed in the URL query string (`service/ai_provider.py:466`). Send it in the `x-goog-api-key` header so it stays out of access logs.

### BE-SEC-14. Information leaks (Medium, S)

- `/docs`, `/redoc` and `/openapi.json` are public in production. Disable them when `APP_ENV=production` or put them behind auth.
- Several handlers return `str(e)` to the client (7 places, for example `auth.py:474`, `service/file.py`). Return a generic message and log the exception with a request ID.
- Login returns 403 "inactive" before checking the password, and `/auth/resend-reset-otp` returns different messages for existing and unknown users. Both allow username enumeration. Return the same response in both cases.
- `uvicorn --forwarded-allow-ips '*'` (`compose.production.yml`) lets any client forge the IP recorded in the audit trail. Restrict to the proxy's address.
- Add `TrustedHostMiddleware` and security headers (HSTS, `X-Frame-Options`, `Referrer-Policy`) at nginx.

### BE-SEC-15. Production data committed to git (High, M)

Tracked files include `Tables_2026-Jun-29_1712.xml` (a 60 MB Caspio export), about 55 CSV exports under `data_migration/` with employee, sales and production data, `List of Accounts - Final.xlsx - Report.csv`, `scripts/active_jobs.csv`, and four files under `static/uploads/`. Move migration inputs to private storage, remove them from the repo and history (same `git filter-repo` run as BE-SEC-06), and add ignore rules for `*.xml`, `*.csv` and `*.xlsx` outside a fixtures folder.

### BE-SEC-16. AI/MCP layer (Medium, M)

The SQL guard in `mcp/sql_query.py` is well built (single statement, keyword and identifier blocklists, read-only transaction, timeout, row cap) and is off by default. Before enabling it in production:
- Run it with a dedicated read-only database role that has `SELECT` on an explicit list of views. A blocklist will miss tables added later, for example `hcp_payroll_report_rows`, `installer_rate_history` and `notifications`, none of which are blocked today.
- The MCP routes require only `reports:read`. Each tool must enforce the permission of the report it wraps.
- The default model IDs in `service/ai_provider.py` (`claude-3-5-sonnet-20241022`) are outdated. Move to a current model and make the ID required configuration instead of a default.
- Log which user asked which question, and decide what data may be sent to an external model provider.

## 4. Phase 2: correctness bugs

### BE-BUG-01. Refresh endpoint name does not match the web client (High, S)

The backend exposes `POST /auth/refresh-token`. The web calls `POST /auth/refresh` (`services/axiosBaseQuery.ts:126`, `store/api/auth.ts:79`), which returns 404, so every refresh fails and the user is sent to login. Once BE-SEC-01 adds token expiry this will log users out every hour. Add `/auth/refresh` as an alias on the backend and fix the web path, then remove the alias later.

Also: a refreshed token does not reset the inactivity clock, so a user who was idle for eight hours gets a new token that is rejected immediately. BE-SEC-09 item 4 fixes this.

### BE-BUG-02. Background tasks use a closed database session (High, M)

Handlers pass the request-scoped `db` to `background_tasks.add_task(save_audit_trail, db, ...)` and `send_notification(db, ...)` in about 23 places, mostly in `routers/auth.py`. FastAPI closes dependency sessions before background tasks run, so these writes use a closed or already-committed session and may fail without anyone noticing. Background functions must open their own session (`save_audit_event(db=None, ...)` already supports this). Remove the `db` parameter from `send_notification`, which does not use it.

### BE-BUG-03. Synchronous endpoints call an async session (High, M)

About 30 routes are plain `def` functions typed `db: Session = Depends(get_db)` that call `db.exec(...)`, `db.get(...)` and `db.commit()` without `await`. `get_db` yields an `AsyncSession`, so these either raise or never commit. Affected: `routers/job_extras.py` (most routes), `operator_workflow.py`, `shop_planning.py`, `shop_planning_section.py`, and the services they call (`TemplatingService`, `service/job.py`). Fifteen of them accept `updated_by: int = 1` as a query parameter, so the caller chooses who the change is attributed to.

For each: check the web and installer app for callers. Delete those with none, and rewrite the rest as `async def` with `current_user`.

### BE-BUG-04. Database health check always passes (Medium, S)

`GET /health/db` (`routers/health.py:23`) calls `db.execute(text("SELECT 1"))` without `await`. It never touches the database and returns "ok" even when Postgres is down. Add `await`. The Docker `HEALTHCHECK` curls `/health`, which redirects to `/health/`; point it at the real path and make it include the database check.

### BE-BUG-05. `return error_response(...)` instead of `raise` (Medium, S)

`utils.helpers.error_response` builds an `HTTPException`. It is returned instead of raised in 41 places (for example `routers/fabs.py:3819`, `templating.py:629`, `jobs.py:322`). A "not found" then becomes a 200 or a 500 with a serialisation error. Search for `return error_response(` and change each to `raise`.

There are also two functions named `success_response` with different signatures (`utils/helpers.py` and `interface/response_wrappers.py`, the second takes `status_code`). Keep one.

### BE-BUG-06. Schedulers start once per worker (Medium, S)

`main.py` starts the monthly report scheduler and the HCP payroll scheduler in every uvicorn worker. `HCP_PAYROLL_SCHEDULER_ENABLED` defaults to `true` and the default command runs 4 workers, so a deployment that forgets to set it to `false` pulls payroll four times and can send four copies of the monthly report. Remove the in-process schedulers and run both from Celery beat, which already exists. Then the separate `monthly_reports` container can go too.

### BE-BUG-07. Swallowed exceptions and `print` (Medium, M)

There are 21 `except Exception: pass` blocks and 32 `print()` calls in `src/`. `call_service` turns every unexpected exception into "Internal server error" and logs only the message, without the stack trace. Use `logger.exception`, add a global exception handler that logs with a request ID, and remove the blanket `pass` blocks unless the reason is written next to them.

### BE-BUG-08. Money stored as floating point (Medium, M)

`revenue`, `gp`, `cost_of_stone`, `cost_per_sqft` and `hourly_rate` are `float`. Totals in the labour cost reports will drift by cents. Migrate these columns to `NUMERIC(12,2)` and use `Decimal` in the report code.

### BE-BUG-09. Timezone model is fragile (Medium, L)

`utils/config.py` monkey-patches SQLModel's `UTCDateTime` so that all `timestamp without time zone` columns hold America/Chicago wall-clock time. The web then patches `Date` globally to match. It works today, but:
- times in the repeated hour at the end of daylight saving are ambiguous, so timer durations that cross 1–2 a.m. on that night can be wrong by an hour;
- a SQLModel upgrade can silently remove the patch (the code already tolerates the import failing);
- every new client (the mobile app, any integration) must copy the convention.

Target state: `timestamptz` columns holding UTC, with API responses carrying an explicit offset. This is a large migration. Until it is scheduled, add a test that fails if the patch stops applying, and compute timer durations from UTC instants.

## 5. Phase 3: performance and scalability

### BE-PERF-01. Missing indexes (High, M)

The baseline migration creates no indexes. `fabs` has indexes only on its primary key and `is_migrated`, yet every list screen filters or joins on `job_id`, `current_stage`, `status_id`, `sales_person_id`, `drafter_id`, the completion dates and `shop_date_schedule`. Foreign keys do not create indexes in PostgreSQL.

1. Run this on production to see what exists, and turn on `pg_stat_statements` to find the slowest queries:
   ```sql
   SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' ORDER BY 1, 2;
   ```
2. Add, using `CREATE INDEX CONCURRENTLY` as in `20261017_120000_add_shop_plan_visibility_indexes.py`:
   - `fabs(job_id)`, `fabs(current_stage, status_id)`, `fabs(sales_person_id)`, `fabs(drafter_id)`, `fabs(shop_date_schedule)`, `fabs(installation_date)`
   - `fab_id` on every per-stage table (templating, drafting, sales CT, slabsmith, final programming, CNC, revisions, install scheduling, install completion, fab notes, timer sessions and events)
   - `business_jobs(account_id)`, `business_jobs(job_number)`
   - `user_roles(user_id)`, `role_permissions(role_id, action_menu_id)`
3. Search uses `ILIKE '%term%'` in 123 places, which cannot use a B-tree index. Add `pg_trgm` GIN indexes on `business_jobs.name`, `business_jobs.job_number` and `accounts.name`.
4. The audit trail filter `request_path ILIKE '%/fabs/{id}%'` (`routers/audit_trails.py`) scans the whole table. Store `fab_id` and `job_id` as indexed columns at write time.

### BE-PERF-02. Connection pool and workers (High, S)

`create_async_engine` uses the defaults (pool of 5, overflow 10) with no `pool_pre_ping`, `pool_recycle` or timeout. `compose.production.yml` runs a single uvicorn worker, while the entrypoint and dev compose run four. Set `pool_size`, `max_overflow`, `pool_pre_ping=True` and `pool_recycle=1800` from the environment, set the worker count explicitly per environment, and check that `workers × (pool_size + max_overflow)` fits inside Postgres `max_connections`. Run gunicorn with uvicorn workers (already in `requirements.txt`) for graceful restarts.

### BE-PERF-03. Extra queries on every request (High, M)

A typical authorised request does: token decode, user select, `UPDATE users` and commit (last activity), roles select, action menu select, permission select, then a separate session and commit for the audit row on writes. That is 5–7 queries before business logic starts.

Change: cache the user's permission set in Redis keyed by `user_id` and `token_version` with a short TTL, and invalidate it when roles change. Move last-activity to Redis. Write audit rows through a Celery task or a batched queue.

### BE-PERF-04. Reports run heavy queries inline (Medium, L)

`routers/reports.py` is 8,530 lines and runs 114 queries inside request handlers, with PDF and XLSX generation on the event loop. The web auto-refreshes list and dashboard queries every 60 seconds per open tab.

- Cache report responses in Redis for 1–5 minutes keyed by parameters.
- Move PDF/XLSX generation to a thread (`run_in_threadpool`) or Celery for large ranges.
- Use materialised views or summary tables refreshed by Celery for monthly and weekly aggregates.
- Add `ETag` and `If-None-Match` to list endpoints so an unchanged auto-refresh costs a 304.

### BE-PERF-05. Unbounded list sizes (Medium, S)

`GET /fabs` allows `limit=1000`, and the web asks for 500–1000 rows in 37 places to fill dropdowns. Add slim lookup endpoints (`/lookups/fabs?search=`, `/lookups/employees`) that return only `id` and a label with server-side search, and cap the main list endpoints at 200.

### BE-PERF-06. Compression and delivery (Low, S)

Enable gzip or brotli for JSON at nginx. Serve file downloads through `X-Accel-Redirect` so nginx streams the bytes after the app authorises the request.

### BE-PERF-07. Real-time updates (Medium, L)

Clients poll every 60 seconds. Add a Server-Sent Events or WebSocket channel backed by Redis pub/sub that pushes "fab changed", "timer changed" and "notification" events, so clients refetch only what changed. This lowers load and is also needed for push notifications in the mobile app.

## 6. Phase 4: architecture and maintainability

### BE-ARCH-01. Break up the large routers (Medium, XL)

`reports.py` (8,530 lines), `fabs.py` (6,345), `shop_cut_plan.py` (2,657) and `operators.py` (1,914) mix HTTP handling, query building and business rules. Routers already call each other's handlers directly (`export_owner_report` calls report handlers as functions, and `update_fab_stage` calls `get_fab`). Move to routers (HTTP only), services (business rules) and repositories or query modules, one package per domain: `fabs/`, `reports/owner/`, `shop/`, `timers/`. Do it one router at a time, starting with whichever is being changed for BE-SEC-04.

### BE-ARCH-02. One stage state machine (Medium, L)

Stage transitions are scattered across `get_next_stage`, `_transition_completed_cutlist_fabs_to_shop`, per-stage routers and `PATCH /fabs/{id}/stage`, which sets any stage with no validation. Define the workflow once: states, allowed transitions, guards and side effects (notifications, audit, timestamps). Every route goes through it. The mobile app will rely on these rules being enforced on the server.

### BE-ARCH-03. Configuration (Medium, M)

Configuration is read with `os.getenv` in many modules with different defaults (`BASE_URL` and `API_BASE_URL`, three upload directory variables). `load_dotenv()` is called in three places and logging is configured twice in `main.py`. Use one `pydantic-settings` `Settings` class that validates at startup and is injected where needed.

### BE-ARCH-04. API consistency (Medium, M)

- Auth, employees, departments, roles and files are served at the root (`/auth`, `/files`), everything else under `/api/v1`. Add `/api/v1` aliases, move the clients, then retire the root paths.
- Three error shapes exist: `{"detail": "..."}`, `{"detail": {"success": false, "message": ...}}` and `{"success": false, ...}`. Add exception handlers that produce one shape for every error, including validation errors.
- Two pagination styles (`skip`/`limit` and `page`/`page_size`) and two schema modules (`business_schemas.py`, `generated_schemas.py`). Pick one of each.
- Add `response_model` everywhere so the OpenAPI document is accurate. Generate TypeScript and Dart clients from it instead of hand-writing 2,800 lines in the web's `store/api/job.ts`.

### BE-ARCH-05. Dependencies (Medium, S)

`requirements.txt` pins only two packages, lists `pytest` and `httpx` twice, and mixes test and runtime dependencies. `passlib` is unmaintained and needs `bcrypt==3.2.2` pinned to keep working. Lock versions with `pip-compile` or `uv`, split dev requirements, replace `passlib` with `argon2-cffi` or direct `bcrypt` (re-hash on next login), and run `pip-audit` in CI.

### BE-ARCH-06. Repository clean-up (Low, M)

The root holds about 40 one-off scripts, test files and notes (`test_*.py`, `add_*.py`, `_debug_chain.py`, `reproduce_issue.py`, a file literally named `\d fabs`, `test_results.json`, two virtualenvs, six overlapping deployment documents). Move the scripts worth keeping into `scripts/` with a README, delete the rest, and merge the deployment documents into one. `docker-compose.yml` is tracked although its own header says it is not; decide which and make the CI workflow match.

## 7. Phase 5: testing, CI/CD and operations

### BE-OPS-01. CI does not run tests (High, M)

The two GitHub workflows SSH into a server as root and run `git pull` followed by `docker compose up --build`. Nothing runs tests, lint or type checks, and production has no workflow.

Change:
1. Add a pull-request workflow: `ruff`, `mypy` on changed modules, `pytest`, `pip-audit`.
2. Build the image once in CI, push it to a registry tagged with the commit SHA, and have servers pull that tag. This makes rollback a tag change and removes the build toolchain from the servers.
3. Deploy with a non-root user.
4. Add a production workflow with a manual approval step.

### BE-OPS-02. Tests run on SQLite, production runs PostgreSQL (High, M)

`tests/conftest.py` uses in-memory SQLite. The code depends on JSONB, partial indexes, `ILIKE`, timezone behaviour and concurrent index creation, none of which SQLite reproduces. Run tests against a PostgreSQL service container. Add tests for the Phase 0 fixes first: token expiry, reset-code attempt limit, file access, the route-walk permission test.

### BE-OPS-03. Migrations are not part of deployment (High, S)

`docker-entrypoint.sh` runs `alembic upgrade head`, but every compose file sets `entrypoint: []`, so migrations never run automatically. Dev mounts `./alembic/versions` from the host, which lets the files on the server differ from the image. Several helper scripts (`sync_schema_to_models.py`, `create_missing_tables.py`, `fix_*_table.py`) change the schema outside Alembic. Make migration an explicit deploy step (`docker compose run --rm web alembic upgrade head`) that must succeed before the new containers start. Add a CI check that `alembic upgrade head` on an empty database produces the same schema as the models, and retire the out-of-band scripts.

### BE-OPS-04. Observability (Medium, M)

Logs are multi-line plain text in a file inside the container. Change to one JSON line per request on stdout with request ID, user ID, route, status and duration. Add Sentry (or equivalent) for exceptions, Prometheus metrics (`prometheus-fastapi-instrumentator`) for latency and pool usage, and alerts on error rate, p95 latency, Celery queue depth and failed payroll ingestion.

### BE-OPS-05. Backups and recovery (High, M)

The repository shows no backup process for PostgreSQL or the uploads volume. Confirm that nightly `pg_dump` or WAL archiving exists, that the uploads directory is backed up off the server, and that a restore has been tested. Redis has no password and no memory limit; set both.

### BE-OPS-06. Staging and production share a host (Medium, M)

Both workflows use the `DEV_VPS_*` secrets, so dev and staging are on one server, and the compose files suggest production is reachable on the same private network (`192.168.1.98`). Confirm that non-production environments cannot reach the production database and that each environment has its own `SECRET_KEY`. Today a dev token would be valid in production if the keys match.

## 8. Order of work

| Order | Items | Outcome |
|---|---|---|
| Week 1 | BE-SEC-01, 02, 05, 06, 07, 10; BE-BUG-01, 04 | Account takeover and token problems closed; all passwords rotated |
| Weeks 2–3 | BE-SEC-03, 04, 08, 09, 11, 12 | Files private; every route authorised; sessions revocable |
| Week 4 | BE-BUG-02, 03, 05, 06; BE-OPS-01, 02, 03 | Dead and broken routes removed; CI runs tests on PostgreSQL |
| Weeks 5–6 | BE-PERF-01, 02, 03, 05; BE-SEC-13, 14, 15 | Indexes, pool settings and caching in place; secrets and data out of git |
| Weeks 7 onward | BE-ARCH-01 to 04; BE-PERF-04, 07; BE-BUG-08, 09; BE-OPS-04 to 06 | Structural work, real-time channel, observability |

Several Phase 0 and Phase 1 items change behaviour that the web and installer app depend on: token expiry and refresh (BE-SEC-01, BE-BUG-01), signed file URLs (BE-SEC-03), and 403 responses where there were none (BE-SEC-04). Ship each together with the matching client change listed in the web and installer documents.

## 9. Open items to check on the servers

These could not be confirmed from the repository:
1. Which indexes exist in production (query in BE-PERF-01).
2. Whether production log files contain request bodies, and who can read them.
3. Whether any account still has a password from the committed scripts.
4. The value of `HCP_PAYROLL_SCHEDULER_ENABLED` and `EOM_STATUS_REPORT_ENABLED` in each environment, and whether duplicate payroll pulls or report emails have happened.
5. Whether a backup and tested restore exist for the database and uploads.
