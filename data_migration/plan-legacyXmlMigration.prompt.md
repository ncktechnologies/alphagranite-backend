## Plan: Legacy XML to AlphaGranite Migration

Migrate legacy Caspio XML exports into the new backend by splitting migration into: (1) reference/master data, (2) core entities (accounts/jobs/fabs), (3) operational history (sessions/events/revisions/notes), with deterministic key mapping, idempotent upserts, and reconciliation reports. Based on current analysis and your choices, we will import full timer/event history, skip direct user assignment during initial load, and migrate trigger results as stored data (not trigger logic).

**Steps**
1. Phase 0 - Source profiling and extraction
1. Parse XML schema and data exports into normalized staging datasets: tables, columns, row counts, null rates, and candidate keys.
1. Build a source catalog for priority tables from your export: `Fab_Status`, `slabsmith_data`, related detail tables (`Shop_Data`, `Draft_Data`, `FP_Data`, `revision_info`), and lookup tables (`Fab_Types`, stone/employee/machine tables if present in export package).
1. Capture quality issues early: duplicate `fab_id`, missing `job_number`, missing account names, invalid dates, and non-numeric values in numeric columns.

2. Phase 1 - Canonical target mapping design (*depends on Phase 0*)
1. Define canonical crosswalks for core identity:
1. `fab_id` (legacy) -> `fabs.id` (or legacy_fab_id shadow column in staging map)
1. `job_number` + account -> `business_jobs`
1. account text -> `accounts.name`
1. legacy enum/type values -> target enum/value sets (`fab_type`, status/stage fields).
1. Build a field-level mapping matrix with 3 statuses per field: Direct, Transform, Not Viable.
1. Confirm unit and semantic conversion rules:
1. time minutes/hours -> seconds for timer session totals.
1. percentage and sqft/linft normalization.
1. date/time timezone normalization (legacy CST-style timestamps -> UTC storage).

3. Phase 2 - Load order and migration mechanics (*depends on Phase 1*)
1. Seed/reference entities first (idempotent upsert): status, departments/roles (if needed), stone types/colors/thickness, edges, fab types, planning/workstation references.
1. Migrate core business entities:
1. accounts -> `accounts`
1. jobs -> `business_jobs`
1. fabs baseline attributes -> `fabs`
1. stage/state fields -> mapped target stage + completion booleans/dates.
1. Migrate operational detail entities:
1. revisions/rework data -> `revisions` and `shop_revisions`
1. notes -> `fab_notes` / `shop_notes` / job notes
1. role-based work sessions -> timer session/event tables (`installer_job_timer_*`, `templater_job_timer_*`, `operator_job_timer_*`, plus drafting session tables as applicable).
1. Run full-history load in deterministic chunks with resume support, idempotent keys, and per-batch commit + failure logging.

4. Phase 3 - Viability handling rules (*parallel with Phase 2 mapping finalization*)
1. Directly viable (import now):
1. core IDs/labels: `fab_id`, job/account identifiers, stone metadata, edge, sqft/pieces.
1. most completion flags/dates: template/draft/slabsmith/sct/final/install completion markers.
1. shop planning metrics: scheduled/completed dates, percent complete, linft/sqft totals.
1. notes fields (shop/install/draft/final/revision) as plain text or note records.
1. timer history from `slabsmith_data` and similar session tables when start/end/duration fields exist.
1. Transform-required viable (import with conversion):
1. boolean flags and integer role references -> target booleans + nullable foreign keys.
1. employee numeric IDs -> nullable user references initially (per your decision), with later backfill via mapping table.
1. legacy formula fields (`fab_percent`, computed dates) -> recompute or map as derived/reporting values, not authoritative source.
1. split/denormalized text columns (machine/employee scheduled text) -> normalized workstation/operator references where possible, else archived note.
1. Not viable for 1:1 import (capture as archive only):
1. Caspio trigger definitions and Blockly XML action layouts (business logic metadata, email workflows).
1. password/auth rows from `Admin_Authentication` (security model mismatch).
1. UI-only helper/sorting formula columns and transient fields with no domain meaning in new schema.

5. Phase 4 - Reconciliation and cutover validation (*depends on Phases 2 and 3*)
1. Reconciliation report by entity: source count, inserted, updated, skipped, errored.
1. Business integrity checks:
1. every migrated fab links to valid job/account.
1. stage completion date consistency (completed flag implies completion date when required).
1. timer totals align with event-derived durations within tolerance.
1. Functional smoke checks against key APIs (fab detail/report/timer/revision endpoints).
1. Produce unresolved reference backlog (unmapped users/machines/types) for backfill run.

6. Phase 5 - Backfill and hardening (*depends on Phase 4*)
1. Apply user/employee mapping table to fill nullable assignee/requester fields.
1. Re-run idempotent importer for corrected rejects.
1. Lock migration artifacts, export audit logs, and document post-cutover guardrails.

**Relevant files**
- `/Users/cugwuh/Documents/Carpediem/ProjectFiles/AlphaGranite/Backend/alphagranite-backend/src/app/interface/generated_schemas.py` — authoritative SQLModel table definitions and constraints.
- `/Users/cugwuh/Documents/Carpediem/ProjectFiles/AlphaGranite/Backend/alphagranite-backend/src/app/routers/reports.py` — report/timer output semantics to preserve during validation.
- `/Users/cugwuh/Documents/Carpediem/ProjectFiles/AlphaGranite/Backend/alphagranite-backend/src/app/routers/shop_revisions.py` — target behavior for shop revision history/pending state.
- `/Users/cugwuh/Documents/Carpediem/ProjectFiles/AlphaGranite/Backend/alphagranite-backend/src/app/utils/timer_guards.py` — pending revision constraints affecting migrated timer usability.
- `/Users/cugwuh/Documents/Carpediem/ProjectFiles/AlphaGranite/Backend/alphagranite-backend/scripts/auto_migrate.py` — schema sync conventions and migration precheck flow.
- `/Users/cugwuh/Documents/Carpediem/ProjectFiles/AlphaGranite/Backend/alphagranite-backend/seed_all.py` — seed/load orchestration pattern to mirror for migration run order.
- `/Users/cugwuh/Documents/Carpediem/ProjectFiles/AlphaGranite/Backend/alphagranite-backend/scripts/seed_accounts.py` — idempotent insert/check pattern for entity imports.
- `/Users/cugwuh/Documents/Carpediem/ProjectFiles/AlphaGranite/Backend/alphagranite-backend/scripts/seed_stone_colors.py` — large-volume reference data loading pattern.

**Verification**
1. Pre-load dry run: generate mapping stats and unresolved lookup lists without writes.
2. Run staged import in non-production database and verify row counts match expected tolerances by table.
3. Execute API-level smoke tests for fab retrieval, dashboard reports, timer session reads, and shop revision checks.
4. Compare sampled legacy records (at least 50 fabs across states) against migrated records for dates, status, notes, and totals.
5. Validate idempotency by re-running importer and confirming no duplicate growth.

**Decisions**
- Include scope: full historical session/event migration.
- Include scope: migrate trigger outcomes as data only.
- Exclude scope (initial pass): direct legacy employee-to-user linkage; leave nullable and backfill later.
- Exclude scope: Caspio automation recreation and legacy auth/password migration.

**Further Considerations**
1. Create a dedicated source-to-target key map table (legacy IDs -> new IDs) to simplify retries and downstream references.
2. Preserve raw legacy payload snapshots per migrated fab for auditability and rollback confidence.
3. Add tolerance thresholds for duration/percent reconciliation before production cutover signoff.