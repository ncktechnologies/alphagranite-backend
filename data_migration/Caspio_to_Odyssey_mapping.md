# Caspio → Odyssey Tracker Migration — Field Mapping (Schema-only phase)

Source: `Caspio_Tables/` (17 CSVs, headers only, 0 data rows as of 2026-09-20).
Target: `odyssey/` (`schema_export.csv` = 69 tables; `od_tracker.sql` DDL).
Old plan adapted: `plan-legacyXmlMigration.prompt.md` (AlphaGranite → renamed to Odyssey; same model).

Full field matrix: `mapping_matrix.csv` (261 rows). Rule legend: **Direct** = copy/cast; **Transform** = conversion needed;
**Transform-Deferred** = needs employee/user map, load nullable or migration-user fallback now, backfill later (per old-plan decision);
**Transform-Archive** = optional derived history, default archive; **Archive** = keep raw in notes/JSONB only; **Skip** = no target.

## 1. Source profiling (Phase 0 — done on schema only)

| Caspio table | Cols | Grain / role | Target family |
|---|---|---|---|
| Fab_Status | 126 | one row per fab (master) | fabs, business_jobs, accounts + all stage tables |
| Draft_Data | 17 | timer sessions per fab | drafting_sessions + drafting_session_notes |
| FP_Data | 15 | timer sessions per fab | final_programming_sessions + notes |
| Shop_Data | 11 | timer/activity rows per fab | operator_job_timer_sessions/events + shop_cut_plans |
| revision_info | 22 | revision rows per fab | revisions (+ files) |
| Fab_Types | 2 | lookup | fab_type |
| Machines_CNC / Cut / Edging | 2 each | lookups | work_stations |
| Alpha_Employees / Employees_Shop / Employees_Template / Active_Sales_Employees | 2–5 | people | users (deferred, nullable/backlog) |
| Default_Shop_Employees | 2 | activity→employee defaults | work_stations seed + operator_ids seed |
| ProductionPerPerson (6), Production_Table_1 (21) | — | daily/person production | Archive by default; optional job_technician_workflows / operation_workflow derived rows |
| Calendar (1) | — | helper | Skip (validation only) |

> No data rows → null rates, dup fab_id, orphan checks are **blocked** until real exports arrive. All conversions below are provisional and must be re-validated in dry run.

## 2. Canonical identity (Phase 1)

- `Fab_Status.fab_id` → `fabs.id` **preserved as PK** (deterministic, idempotent). Reset `fabs_id_seq` after load. Key-map table `legacy_fab_map(fab_id, new_id)` still logged for audit even when ids equal.
- `Fab_Status.account` → `accounts.name` upsert (unique index `ix_accounts_name`; trim + case-normalize; blank → `UNASSIGNED-<job_number>` + reject log).
- `Fab_Status.job_number` → `business_jobs.job_number` upsert; `account_id` from accounts map; `name` = job_name else `JOB-<fab_id>`; `sq_ft`/`project_value` = SUM over fabs per job (not per-row copy); `start_date` = MIN creation_date.
- `stone_type/color/thickness/edge` → upsert `stone_types` / `stone_colors` / `stone_thickness` / `edges` by name; `fabs.*_id` resolved via map. Unmapped → block fab insert, park in reject table (do NOT silently null; these are NOT NULL in fabs).
- `fab_type` → upsert `fab_type.name`; `fabs.fab_type` is varchar so copy normalized name directly.
- `sales_person/installer/drafter/by` fields → **deferred** (old-plan decision): load NULL or migration-user fallback where column is NOT NULL (`sales_cts.drafter_id`, `final_programmings.drafter_id`, timer `operator_id/user_id`, `revisions.requested_by`), record every fallback in `unresolved_reference_backlog`.

## 3. Stage mapping summary (Fab_Status 126 cols)

- Template → `templatings` (1 row/fab) + `fabs.template_needed (!not_needed)`, `template_received`, `template_completed_date`.
- Draft / pre-draft → `pre_draft_reviews` (only if any pre_draft field set) + `draftings` (1 row/fab) + `fabs.drafting_needed (!not_needed)`, `draft_completed`, `draft_completed_date`, `predraft_completed_date`; notes → `draftings.draft_note` + `fab_notes(stage=draft)`.
- SlabSmith → `slab_smiths` (1 row/fab, type=CUST default) + `fabs.slab_smith_cust_needed`, `slab_smith_ag_needed` (inverted), `slab_smith_used`, `slabsmith_completed_date`; notes → `fab_notes(stage=slabsmith)`.
- SCT → `sales_cts` (1 row/fab, slab_smith_type=SCT) + `fabs.sct_needed (!not_needed)`, `sct_completed`, `sct_completed_date` (= `sales_ct_completed_date`).
- Final programming → `final_programmings` (1 row/fab) + `fabs.final_programming_needed (!not_needed)`, `fp_not_needed` direct, `final_programming_complete`, `final_programming_completed_date`; notes → `fab_notes(stage=final_programming)`.
- Shop planning → `shop_plannings` (1 row/fab) + `fabs.shop_date_schedule`, `shop_est_completion_date` (prefer `shop_date_scheduled2`); pre_shop_review → completed_steps derivation; pre_shop text → `fab_notes(stage=shop)`.
- Resurface → `resurface_schedulings` (only if any resurface field set); percent → completed_sqft derivation, raw kept in notes JSONB.
- Cut → `cut_list` (1 row/fab) + `shop_cut_plans` workstation=CUT row; machine/employee → `shop_planning_sections.machine` / `operator_ids` (deferred).
- WJ → `fabs.wj_time_minutes`, `wj_linft` + `wj_schedulings` + `wj_programmings` (1 row each/fab if any wj field set).
- Edging/Miter/CNC/QC → `fabs.{edging,cnc,miter}_linft` + one `shop_cut_plans` row per workstation (EDGING/MITER/CNC/QC) with scheduled/estimated/percent/completed dates; machine → planning_sections.machine; employee → deferred.
- Install → `install_schedulings` + `install_completions` + `fabs.installation_date` (prefer completion_date, fallback install_date; install_date2 archived); installer deferred; install_confirmed → is_confirmed; notes → fab_notes(stage=install) + schedulings.notes JSONB.
- Closeout/money → `fabs.revenue`, `gp`, `cost_of_stone` (float) + `cost_of_stones` row (varchar mirror) + `business_jobs.project_value` = SUM; `cost_entered` → cost row is_completed; `complete` → `status_id` via status.value_id map + cut_list.is_completed mirror.
- Redo → `revisions` row (type=SHOP default, department=redo_dept, person_name=redo_person, redo_cost archived in revision_notes as `REDO COST=`); `fabs.redo_department` / `redo_requested_by` deferred; **known mismatch**: no money target for redo_cost → do NOT put cost into `redo_total_sqft` (sqft col); leave null + flag.
- Formula/UI cols (`fab_percent`, `*_clock_complete`, `*_date_completed_2`, `estimated_completion_date2`, `first_est_completion_date`) → archive into `fabs.notes` JSONB, never authoritative.
- No-source fabs cols (`saw_cut_lnft`, `saw_miter_lnft`, `wj_miter_lnft`, `slabsmith_time_minutes`, `drafter_*`, approvals, `current_stage/next_stage` if empty) → null or derive current/next stage from latest completed stage flag.

## 4. Session/history mapping (Draft/FP/Shop)

- Draft_Data → `drafting_sessions` (prefer computed start/end duration in seconds; state+active_session → status; open if end null) + `drafting_session_notes` for old/new_duration, temp, intermediary, test cols.
- FP_Data → `final_programming_sessions` + `final_programming_session_notes`, same rules.
- Shop_Data → `operator_job_timer_sessions`/`operator_job_timer_events` (activity → work_stations.id map; employee deferred; duration text→seconds, prefer computed; measure/units/percent → event notes + matched `shop_cut_plans.work_percentage`).
- revision_info → `revisions` (type normalized, completed by date) + `files` row only if FileData non-empty; Account/Job/Stone cols are cross-checks (Fab_Status wins, mismatches logged, no dup accounts).

## 5. Load order + idempotency (Phase 2, adapted)

1. Seeds/defaults: `status`, `departments`, `planning_sections`, `work_stations` (from Machines_* + Default_Shop_Employees), `service_level_settings` — upsert, no Caspio source.
2. References: `fab_type`, `stone_types`, `stone_colors`, `stone_thickness`, `edges`, `accounts` — upsert by natural key (name/thickness).
3. Core: `business_jobs` (by job_number) → `fabs` (by preserved id) → `cost_of_stones`, `cut_list`, stage 1-rows (`templatings`, `draftings`, `pre_draft_reviews?`, `slab_smiths`, `sales_cts`, `final_programmings`, `wj_schedulings`, `wj_programmings`, `resurface_schedulings`, `install_schedulings`, `install_completions`, `shop_plannings`, `shop_cut_plans` ×5, `shop_planning_sections`) — all idempotent `INSERT … ON CONFLICT DO UPDATE`.
4. History: `revisions`/`shop_revisions` (Fab_Status redo + revision_info), `fab_notes`/`shop_notes`/`job_notes`, timer sessions + events/notes tables — chunked, deterministic, resume on (fab_id, session_start).
5. Users deferred: `users` skeleton from 4 employee files (ClockNum→hcp_employee_id, username dedup, NO passwords) → backfill pass fills `*_by/technician/drafter/operator` FKs; every fallback recorded.
6. Post-load: `SELECT setval('fabs_id_seq', max(id))`, re-run importer → zero growth (idempotency proof), reconciliation counts.

## 6. Reconciliation + backlog (Phase 4/5)

- Per-entity: source count / inserted / updated / skipped / errored; orphan fab_ids (sessions/revisions without fabs row) → reject table, never cascade-create fabs.
- Integrity: every fab → valid job/account + stone/edge FKs; completed flag ⇒ date present (where required); timer totals vs event durations within tolerance; 50-fab sample (dates/status/notes/totals) vs legacy.
- Unresolved backlog tables: unmapped users/machines/stone-edge variants, `redo_total_sqft` cost-vs-sqft flags, formula-col archive audit, raw payload snapshot per fab (`fabs.notes->_migrated_raw` or sidecar table) for rollback confidence.
- Blocked until data arrives: dup fab_id, null-rate stats, timezone proof (assume CST→UTC naive), minutes/hours→seconds unit proof.

## 7. What to ask for next

Real Caspio data exports (same 17 files with rows), plus: `status` seed values (value_ids for COMPLETED/IN_PROGRESS), `departments` list (to map redo_dept), and confirmation that preserving `fab_id` as `fabs.id` is acceptable (else switch to key-map with new serials).
