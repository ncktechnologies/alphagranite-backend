# Reporting Roadmap - Alpha Granite

This document defines owner-focused reports that are now available in the API and the next phase to align with client workbook formats.

## Phase 1 - Implemented API Reports

Base route prefix: `/api/v1/reports/owner`

1. `GET /overview`
- Purpose: Executive snapshot of jobs, fabs, install pipeline, revenue, and gross profit.
- Filters: `start_date`, `end_date` (ISO date)
- Use case: Daily owner pulse and month-to-date business health.

2. `GET /redo-analysis`
- Purpose: Track redo/revision rate and identify account/job hotspots.
- Filters: `start_date`, `end_date`, `top_n`
- Use case: Margin protection and root-cause tracking for rework.

3. `GET /shop-status`
- Purpose: Stage-level WIP count, average/max aging, and stalled item count (>14 days).
- Filters: `start_date`, `end_date`
- Use case: Shop bottleneck management and SLA risk.

4. `GET /install-performance`
- Purpose: Installer productivity with completed installs, sqft, work hours, and sqft/hour.
- Filters: `start_date`, `end_date`, `top_n`
- Use case: Crew planning, labor productivity, and coaching.

5. `GET /weekly-trends`
- Purpose: Weekly trendline for fabs created, installs completed, revenue, GP, and installed sqft.
- Filters: `weeks`
- Use case: Operational trend visibility and forecasting.

## Workbook-to-Platform Mapping

Client sample workbook themes are covered as follows:

- 2025 REDO REPORT -> `/redo-analysis`
- END OF MONTH SHOP STATUS REPORT -> `/shop-status`
- Install Report -> `/install-performance` and `/weekly-trends`
- Installer Labor Cost -> `/install-performance` (hours and output basis)
- Workshop Weekly Analysis -> `/weekly-trends` and `/shop-status`

## Phase 2 - Recommended Enhancements

1. Add report snapshots for historical immutability.
- Suggested table: `report_snapshots(report_key, period_start, period_end, payload_json, generated_at)`

2. Add drill-down endpoints per report row.
- Example: from account redo hotspot to list of affected fabs/jobs.

3. Add scheduled report delivery.
- Daily/weekly email dispatch with attached exports for owner and managers.

## Phase 2 - Implemented Now

1. Labor cost model added.
- New table/model: `installer_rate_history(installer_id, hourly_rate, effective_from, effective_to, is_active)`
- New endpoints:
	- `GET /api/v1/reports/owner/installer-rates`
	- `POST /api/v1/reports/owner/installer-rates`

2. Install performance now includes labor metrics.
- Per installer: `hourly_rate`, `labor_cost`, `labor_cost_per_sqft`
- Summary: `total_labor_cost`, `portfolio_labor_cost_per_sqft`

3. Export endpoints added.
- `GET /api/v1/reports/owner/export/{report_key}?export_format=csv|xlsx|json`

4. Management packet endpoint added.
- `GET /api/v1/reports/owner/management-packet`
- Bundles overview, redo analysis, shop status, install performance, and weekly trends.

## Data Quality Notes

- Some sqft fields are stored as strings in source tables; report code safely parses numeric values.
- Revenue and GP are currently read from FAB records and summarized by period.
- Install labor hours come from installer timer sessions.

## Suggested Rollout Sequence

1. Validate report results with owner for last 4-8 weeks.
2. Freeze KPI definitions (single source of truth).
3. Implement phase-2 labor cost and exports.
4. Automate weekly management packet.
