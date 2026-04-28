from __future__ import annotations
# pyright: reportGeneralTypeIssues=false, reportMissingImports=false

import csv
import calendar
import io
import json
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import and_, case, func, literal_column, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import get_db
from src.app.database.account import Account
from src.app.database.business_job import BusinessJob
from src.app.database.department import Department
from src.app.database.fab import Fab
from src.app.database.installer_rate_history import InstallerRateHistory
from src.app.database.installer_job_timer_session import InstallerJobTimerSession
from src.app.database.stone_color import StoneColor
from src.app.database.stone_thickness import StoneThickness
from src.app.database.stone_type import StoneType
from src.app.database.user import User
from src.app.interface.generated_schemas import CostOfStone, CutList, InstallCompletion, InstallScheduling, Revision, Templating
from src.app.interface.response_wrappers import SuccessResponse, success_response
from src.app.middleware.jwt_auth import get_current_user

router = APIRouter()


class InstallerRateUpsert(BaseModel):
    installer_id: int = Field(..., gt=0)
    hourly_rate: float = Field(..., gt=0)
    effective_from: datetime
    effective_to: Optional[datetime] = None
    is_active: bool = True


@router.get("/reports/redos", response_model=SuccessResponse[list[dict]])
async def get_ag_redo_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return AG REDO FAB rows with complete report fields."""
    rows = (
        await db.execute(
            select(
                Fab.created_at,
                Fab.fab_type,
                Fab.id,
                BusinessJob.job_number,
                Account.name,
                BusinessJob.name,
                StoneType.name,
                StoneColor.name,
                StoneThickness.thickness,
                Fab.no_of_pieces,
                Fab.total_sqft,
                CostOfStone.cost_per_sqft,
                Revision.revision_notes,
            )
            .select_from(Fab)
            .join(BusinessJob, BusinessJob.id == Fab.job_id, isouter=True)
            .join(Account, Account.id == BusinessJob.account_id, isouter=True)
            .join(StoneType, StoneType.id == Fab.stone_type_id, isouter=True)
            .join(StoneColor, StoneColor.id == Fab.stone_color_id, isouter=True)
            .join(StoneThickness, StoneThickness.id == Fab.stone_thickness_id, isouter=True)
            .join(CostOfStone, CostOfStone.id == Fab.cost_of_stone_id, isouter=True)
            .join(Revision, Revision.fab_id == Fab.id, isouter=True)
            .where(func.lower(Fab.fab_type) == "ag redo")
            .order_by(Fab.created_at.desc(), Fab.id.desc())
        )
    ).all()

    departments = (await db.execute(select(Department.name).order_by(Department.name.asc()))).all()
    department_options = [row[0] for row in departments if row[0]]

    data = []
    for (
        created_at,
        fab_type,
        fab_id,
        job_number,
        account_name,
        job_name,
        stone_type,
        stone_color,
        stone_thickness,
        no_of_pieces,
        sqft,
        cost_per_sqft_raw,
        revision_notes,
    ) in rows:
        cost_per_sqft = round(_to_float(cost_per_sqft_raw), 2) if cost_per_sqft_raw is not None else None
        sqft_value = round(_to_float(sqft), 2)
        total_cost = round(cost_per_sqft * sqft_value * 2.1, 2) if cost_per_sqft is not None else None

        info_parts = [
            account_name,
            job_name,
            stone_type,
            stone_color,
            stone_thickness,
        ]
        fab_info = " - ".join(str(part).strip() for part in info_parts if part and str(part).strip()) or None

        data.append(
            {
                "fab_created_date": created_at.date().isoformat() if created_at else None,
                "fab_type": fab_type,
                "fab_id": fab_id,
                "job_number": job_number,
                "fab_info": fab_info,
                "no_of_pieces": int(_to_float(no_of_pieces)),
                "sqft": sqft_value,
                "cost_per_sqft": cost_per_sqft,
                "total_cost": total_cost,
                "department": None,
                "person_name": None,
                "reason": revision_notes,
                "department_options": department_options,
            }
        )

    return success_response(data, "AG REDO report data retrieved successfully")


def _range_bounds(start_date: Optional[date], end_date: Optional[date]) -> tuple[Optional[datetime], Optional[datetime]]:
    start_dt = datetime.combine(start_date, time.min) if start_date else None
    end_dt = datetime.combine(end_date, time.max) if end_date else None
    return start_dt, end_dt


def _month_bounds(year: int, month: int) -> tuple[datetime, datetime]:
    start_dt = datetime(year, month, 1)
    if month == 12:
        end_dt = datetime(year + 1, 1, 1) - timedelta(microseconds=1)
    else:
        end_dt = datetime(year, month + 1, 1) - timedelta(microseconds=1)
    return start_dt, end_dt


def _parse_month_input(month_value: str) -> Optional[int]:
    text = (month_value or "").strip()
    if not text:
        return None

    if text.isdigit():
        month_num = int(text)
        return month_num if 1 <= month_num <= 12 else None

    lower = text.lower()
    for idx, name in enumerate(calendar.month_name):
        if idx == 0:
            continue
        if lower == name.lower():
            return idx
    for idx, name in enumerate(calendar.month_abbr):
        if idx == 0:
            continue
        if lower == name.lower():
            return idx

    return None


def _days_between(start_value: Optional[datetime], end_value: Optional[datetime]) -> Optional[int]:
    if start_value is None or end_value is None:
        return None
    return max((end_value.date() - start_value.date()).days, 0)


def _apply_datetime_filters(filters: list, field, start_dt: Optional[datetime], end_dt: Optional[datetime]) -> None:
    if start_dt is not None:
        filters.append(field >= start_dt)
    if end_dt is not None:
        filters.append(field <= end_dt)


def _to_float(value) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _rows_from_mapping(value: dict) -> list[dict]:
    return [{"metric": k, "value": v} for k, v in value.items()]


def _format_duration_hhmm(total_seconds: int) -> str:
    safe_seconds = max(int(total_seconds or 0), 0)
    hours = safe_seconds // 3600
    minutes = (safe_seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"


def _notes_to_text(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, list):
        joined = " | ".join(str(item).strip() for item in value if str(item).strip())
        return joined or None
    text = str(value).strip()
    return text or None


def _client_layout_sections(report_key: str, data: dict) -> Optional[list[tuple[str, list[dict]]]]:
    if report_key == "redo-analysis":
        period = data.get("period", {})
        summary = data.get("summary", {})
        redo_by_stage = data.get("redo_by_stage", [])
        accounts = data.get("top_accounts_with_redo", [])
        jobs = data.get("top_jobs_with_redo", [])

        total_redo = sum(int(_to_float(row.get("redo_count", 0))) for row in redo_by_stage) or 0
        stage_rows = []
        for row in redo_by_stage:
            stage_count = int(_to_float(row.get("redo_count", 0)))
            stage_rows.append(
                {
                    "stage": row.get("stage"),
                    "redo_count": stage_count,
                    "redo_share_percent": round((stage_count / total_redo) * 100, 2) if total_redo else 0.0,
                }
            )

        hotspot_rows = []
        for idx, row in enumerate(accounts, start=1):
            hotspot_rows.append(
                {
                    "rank": idx,
                    "category": "Account",
                    "reference": row.get("account_id"),
                    "name": row.get("account_name"),
                    "redo_count": int(_to_float(row.get("redo_count", 0))),
                    "redo_revenue": round(_to_float(row.get("redo_revenue", 0)), 2),
                }
            )
        for idx, row in enumerate(jobs, start=1):
            hotspot_rows.append(
                {
                    "rank": idx,
                    "category": "Job",
                    "reference": row.get("job_number") or row.get("job_id"),
                    "name": row.get("job_name"),
                    "redo_count": int(_to_float(row.get("redo_count", 0))),
                    "redo_revenue": "",
                }
            )

        summary_rows = [
            {
                "period_start": period.get("start_date"),
                "period_end": period.get("end_date"),
                "total_fabs": int(_to_float(summary.get("total_fabs", 0))),
                "revised_fabs": int(_to_float(summary.get("revised_fabs", 0))),
                "redo_rate_percent": round(_to_float(summary.get("redo_rate_percent", 0)), 2),
                "revision_events": int(_to_float(summary.get("revision_events", 0))),
            }
        ]

        return [
            ("redo_summary", summary_rows),
            ("redo_by_stage", stage_rows),
            ("redo_hotspots", hotspot_rows),
        ]

    if report_key == "shop-status":
        period = data.get("period", {})
        stage_rows = []
        for row in data.get("stage_status", []):
            fab_count = int(_to_float(row.get("fab_count", 0)))
            stalled_count = int(_to_float(row.get("stalled_over_14_days", 0)))
            stage_rows.append(
                {
                    "stage": row.get("stage"),
                    "fab_count": fab_count,
                    "avg_age_days": round(_to_float(row.get("avg_age_days", 0)), 2),
                    "max_age_days": round(_to_float(row.get("max_age_days", 0)), 2),
                    "stalled_over_14_days": stalled_count,
                    "stalled_rate_percent": round((stalled_count / fab_count) * 100, 2) if fab_count else 0.0,
                }
            )

        alerts_rows = []
        for row in stage_rows:
            if row["stalled_over_14_days"] <= 0:
                continue
            stalled_rate = _to_float(row["stalled_rate_percent"])
            priority = "high" if stalled_rate >= 30 else "medium" if stalled_rate >= 15 else "low"
            alerts_rows.append(
                {
                    "stage": row["stage"],
                    "priority": priority,
                    "stalled_over_14_days": row["stalled_over_14_days"],
                    "stalled_rate_percent": row["stalled_rate_percent"],
                }
            )

        cover_rows = [
            {
                "report": "End of Month Shop Status",
                "period_start": period.get("start_date"),
                "period_end": period.get("end_date"),
                "generated_at": datetime.now().isoformat(),
            }
        ]

        return [
            ("report_cover", cover_rows),
            ("shop_status", stage_rows),
            ("shop_alerts", alerts_rows),
        ]

    return None


def _report_sections(report_key: str, data: dict, layout: str = "default") -> list[tuple[str, list[dict]]]:
    if layout == "client":
        sections = _client_layout_sections(report_key, data)
        if sections is not None:
            return sections

    if report_key == "overview":
        kpi_rows = _rows_from_mapping(data.get("kpis", {}))
        return [
            ("kpis", kpi_rows),
            ("stage_breakdown", data.get("stage_breakdown", [])),
        ]

    if report_key == "redo-analysis":
        summary_rows = _rows_from_mapping(data.get("summary", {}))
        return [
            ("summary", summary_rows),
            ("redo_by_stage", data.get("redo_by_stage", [])),
            ("top_accounts_with_redo", data.get("top_accounts_with_redo", [])),
            ("top_jobs_with_redo", data.get("top_jobs_with_redo", [])),
        ]

    if report_key == "shop-status":
        return [("stage_status", data.get("stage_status", []))]

    if report_key == "install-performance":
        summary_rows = _rows_from_mapping(data.get("summary", {}))
        return [
            ("summary", summary_rows),
            ("installer_breakdown", data.get("installer_breakdown", [])),
        ]

    if report_key == "installation-template":
        summary_rows = _rows_from_mapping(data.get("summary", {}))
        return [
            ("summary", summary_rows),
            ("installation_template_rows", data.get("rows", [])),
        ]

    if report_key == "monthly-install-completion":
        summary_rows = _rows_from_mapping(data.get("summary", {}))
        return [
            ("summary", summary_rows),
            ("daily_totals", data.get("daily_totals", [])),
            ("rows", data.get("rows", [])),
        ]

    if report_key == "daily-install-completion":
        summary_rows = _rows_from_mapping(data.get("summary", {}))
        return [
            ("summary", summary_rows),
            ("daily_totals", data.get("daily_totals", [])),
            ("rows", data.get("rows", [])),
        ]

    if report_key == "monthly-cut-completion":
        summary_rows = _rows_from_mapping(data.get("summary", {}))
        return [
            ("summary", summary_rows),
            ("daily_totals", data.get("daily_totals", [])),
            ("rows", data.get("rows", [])),
        ]

    if report_key == "turnaround-times":
        stats_rows = _rows_from_mapping(data.get("summary", {}))
        return [
            ("summary", stats_rows),
            ("rows", data.get("rows", [])),
        ]

    if report_key == "service-level":
        summary_rows = _rows_from_mapping(data.get("summary", {}))
        widget_rows = []
        widgets = data.get("widgets", {})
        if widgets:
            for metric_key, metric_value in widgets.items():
                if isinstance(metric_value, dict):
                    widget_rows.append({"metric": metric_key, "value": json.dumps(metric_value)})
                else:
                    widget_rows.append({"metric": metric_key, "value": metric_value})
        return [
            ("widgets", widget_rows),
            ("summary", summary_rows),
            ("stage_bottleneck_heat_map", data.get("stage_bottleneck_heat_map", [])),
            ("fab_status_rows", data.get("fab_status_rows", [])),
            ("cycle_time_stats", data.get("cycle_time_stats", [])),
            ("aging_backlog", data.get("aging_backlog", [])),
            ("breach_details", data.get("breach_details", [])),
        ]

    if report_key == "weekly-trends":
        return [("weekly_trends", data.get("weekly_trends", []))]

    if report_key == "management-packet":
        rows = []
        for block_name, block_value in data.items():
            if isinstance(block_value, dict):
                rows.append({"section": block_name, "payload": json.dumps(block_value)})
            else:
                rows.append({"section": block_name, "payload": str(block_value)})
        return [("packet", rows)]

    return [("data", [{"payload": json.dumps(data)}])]


def _csv_bytes(report_key: str, data: dict, layout: str = "default") -> bytes:
    sections = _report_sections(report_key, data, layout=layout)
    buf = io.StringIO()
    writer = csv.writer(buf)

    for section_name, rows in sections:
        writer.writerow([section_name])
        if not rows:
            writer.writerow(["no_data"])
            writer.writerow([])
            continue

        headers = sorted({k for row in rows for k in row.keys()})
        writer.writerow(headers)
        for row in rows:
            writer.writerow([row.get(h, "") for h in headers])
        writer.writerow([])

    return buf.getvalue().encode("utf-8")


def _xlsx_bytes(report_key: str, data: dict, layout: str = "default") -> bytes:
    from openpyxl import Workbook  # type: ignore[reportMissingImports]

    sections = _report_sections(report_key, data, layout=layout)
    wb = Workbook()
    # Remove the default sheet and create one per section.
    active_sheet = wb.active
    if active_sheet is not None:
        wb.remove(active_sheet)

    for idx, (section_name, rows) in enumerate(sections):
        ws = wb.create_sheet(title=section_name[:31] or f"sheet_{idx + 1}")
        if not rows:
            ws.cell(row=1, column=1, value="no_data")
            continue

        headers = sorted({k for row in rows for k in row.keys()})
        for col_idx, header in enumerate(headers, start=1):
            ws.cell(row=1, column=col_idx, value=header)

        for row_idx, row in enumerate(rows, start=2):
            for col_idx, header in enumerate(headers, start=1):
                ws.cell(row=row_idx, column=col_idx, value=str(row.get(header, "")))

    out = io.BytesIO()
    wb.save(out)
    out.seek(0)
    return out.read()


def _unwrap_success_data(response) -> dict:
    payload = json.loads(response.body.decode("utf-8"))
    return payload.get("data", {})


@router.get("/reports/owner/overview", response_model=SuccessResponse[dict])
async def get_owner_overview_report(
    start_date: Optional[date] = Query(None, description="Inclusive start date filter"),
    end_date: Optional[date] = Query(None, description="Inclusive end date filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Owner summary KPIs across jobs, fabs, finance, and install pipeline."""
    start_dt, end_dt = _range_bounds(start_date, end_date)

    fab_filters = []
    _apply_datetime_filters(fab_filters, Fab.created_at, start_dt, end_dt)

    job_filters = []
    _apply_datetime_filters(job_filters, BusinessJob.created_at, start_dt, end_dt)

    completed_install_filters = [Fab.current_stage == "install_completion"]
    _apply_datetime_filters(completed_install_filters, Fab.updated_at, start_dt, end_dt)

    pending_install_filters = [
        or_(
            Fab.current_stage == "install_scheduling",
            Fab.current_stage == "resurface_scheduling",
        )
    ]
    _apply_datetime_filters(pending_install_filters, Fab.created_at, start_dt, end_dt)

    active_fab_filters = [Fab.status_id == 1]
    _apply_datetime_filters(active_fab_filters, Fab.created_at, start_dt, end_dt)

    total_jobs = (
        await db.execute(select(func.count(BusinessJob.id)).where(and_(*job_filters)) if job_filters else select(func.count(BusinessJob.id)))
    ).scalar() or 0
    total_fabs = (
        await db.execute(select(func.count(Fab.id)).where(and_(*fab_filters)) if fab_filters else select(func.count(Fab.id)))
    ).scalar() or 0

    completed_installs = (
        await db.execute(select(func.count(Fab.id)).where(and_(*completed_install_filters)))
    ).scalar() or 0
    pending_installs = (
        await db.execute(select(func.count(Fab.id)).where(and_(*pending_install_filters)))
    ).scalar() or 0
    active_fabs = (
        await db.execute(select(func.count(Fab.id)).where(and_(*active_fab_filters)))
    ).scalar() or 0

    revenue_filters = [Fab.revenue.isnot(None)]
    _apply_datetime_filters(revenue_filters, Fab.created_at, start_dt, end_dt)
    total_revenue = (
        await db.execute(select(func.sum(Fab.revenue)).where(and_(*revenue_filters)))
    ).scalar() or 0

    gp_filters = [Fab.gp.isnot(None)]
    _apply_datetime_filters(gp_filters, Fab.created_at, start_dt, end_dt)
    total_gp = (
        await db.execute(select(func.sum(Fab.gp)).where(and_(*gp_filters)))
    ).scalar() or 0

    stage_query = (
        select(Fab.current_stage, func.count(Fab.id).label("count"))
        .group_by(Fab.current_stage)
        .order_by(func.count(Fab.id).desc())
    )
    if fab_filters:
        stage_query = stage_query.where(and_(*fab_filters))

    stage_rows = (await db.execute(stage_query)).all()
    stage_breakdown = [
        {"stage": row[0] or "unknown", "count": row[1]} for row in stage_rows
    ]

    completion_rate = round((completed_installs / total_fabs) * 100, 2) if total_fabs else 0.0
    gp_margin = round((_to_float(total_gp) / _to_float(total_revenue)) * 100, 2) if _to_float(total_revenue) else 0.0

    return success_response(
        {
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
            "kpis": {
                "total_jobs": total_jobs,
                "total_fabs": total_fabs,
                "active_fabs": active_fabs,
                "pending_installs": pending_installs,
                "completed_installs": completed_installs,
                "completion_rate_percent": completion_rate,
                "total_revenue": round(_to_float(total_revenue), 2),
                "gross_profit": round(_to_float(total_gp), 2),
                "gross_margin_percent": gp_margin,
            },
            "stage_breakdown": stage_breakdown,
        },
        "Owner overview report generated",
    )


@router.get("/reports/owner/redo-analysis", response_model=SuccessResponse[dict])
async def get_owner_redo_analysis_report(
    start_date: Optional[date] = Query(None, description="Inclusive start date filter"),
    end_date: Optional[date] = Query(None, description="Inclusive end date filter"),
    top_n: int = Query(10, ge=1, le=50, description="Top N groups to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze redo/revision volume and hotspots by stage, account, and job."""
    start_dt, end_dt = _range_bounds(start_date, end_date)

    fab_filters = []
    _apply_datetime_filters(fab_filters, Fab.created_at, start_dt, end_dt)

    total_fabs = (
        await db.execute(select(func.count(Fab.id)).where(and_(*fab_filters)) if fab_filters else select(func.count(Fab.id)))
    ).scalar() or 0

    revised_filters = [Fab.revised.is_(True)]
    revised_filters.extend(fab_filters)
    revised_count = (
        await db.execute(select(func.count(Fab.id)).where(and_(*revised_filters)))
    ).scalar() or 0

    revision_filters = []
    _apply_datetime_filters(revision_filters, Revision.created_at, start_dt, end_dt)
    revision_events = (
        await db.execute(
            select(func.count(Revision.id)).where(and_(*revision_filters)) if revision_filters else select(func.count(Revision.id))
        )
    ).scalar() or 0

    stage_redo_query = (
        select(Fab.current_stage, func.count(Fab.id).label("redo_count"))
        .where(Fab.revised.is_(True))
        .group_by(Fab.current_stage)
        .order_by(func.count(Fab.id).desc())
    )
    if fab_filters:
        stage_redo_query = stage_redo_query.where(and_(*fab_filters))

    stage_redo = [
        {"stage": row[0] or "unknown", "redo_count": row[1]}
        for row in (await db.execute(stage_redo_query)).all()
    ]

    account_hotspot_query = (
        select(
            Account.id,
            Account.name,
            func.count(Fab.id).label("redo_count"),
            func.sum(Fab.revenue).label("redo_revenue"),
        )
        .select_from(Fab)
        .join(BusinessJob, BusinessJob.id == Fab.job_id)
        .join(Account, Account.id == BusinessJob.account_id, isouter=True)
        .where(Fab.revised.is_(True))
        .group_by(Account.id, Account.name)
        .order_by(func.count(Fab.id).desc())
        .limit(top_n)
    )
    if fab_filters:
        account_hotspot_query = account_hotspot_query.where(and_(*fab_filters))

    account_hotspots = [
        {
            "account_id": row[0],
            "account_name": row[1] or "Unassigned Account",
            "redo_count": row[2],
            "redo_revenue": round(_to_float(row[3]), 2),
        }
        for row in (await db.execute(account_hotspot_query)).all()
    ]

    job_hotspot_query = (
        select(
            BusinessJob.id,
            BusinessJob.job_number,
            BusinessJob.name,
            func.count(Fab.id).label("redo_count"),
        )
        .select_from(Fab)
        .join(BusinessJob, BusinessJob.id == Fab.job_id)
        .where(Fab.revised.is_(True))
        .group_by(BusinessJob.id, BusinessJob.job_number, BusinessJob.name)
        .order_by(func.count(Fab.id).desc())
        .limit(top_n)
    )
    if fab_filters:
        job_hotspot_query = job_hotspot_query.where(and_(*fab_filters))

    job_hotspots = [
        {
            "job_id": row[0],
            "job_number": row[1],
            "job_name": row[2],
            "redo_count": row[3],
        }
        for row in (await db.execute(job_hotspot_query)).all()
    ]

    redo_rate = round((revised_count / total_fabs) * 100, 2) if total_fabs else 0.0

    return success_response(
        {
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
            "summary": {
                "total_fabs": total_fabs,
                "revised_fabs": revised_count,
                "redo_rate_percent": redo_rate,
                "revision_events": revision_events,
            },
            "redo_by_stage": stage_redo,
            "top_accounts_with_redo": account_hotspots,
            "top_jobs_with_redo": job_hotspots,
        },
        "Owner redo analysis report generated",
    )


@router.get("/reports/owner/shop-status", response_model=SuccessResponse[dict])
async def get_owner_shop_status_report(
    start_date: Optional[date] = Query(None, description="Inclusive start date filter"),
    end_date: Optional[date] = Query(None, description="Inclusive end date filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Current shop load by stage with aging and stalled-work indicators."""
    start_dt, end_dt = _range_bounds(start_date, end_date)

    filters = []
    _apply_datetime_filters(filters, Fab.created_at, start_dt, end_dt)

    age_days_expr = func.date_part("day", func.now() - func.coalesce(Fab.updated_at, Fab.created_at))
    stage_query = (
        select(
            Fab.current_stage,
            func.count(Fab.id).label("fab_count"),
            func.avg(age_days_expr).label("avg_age_days"),
            func.max(age_days_expr).label("max_age_days"),
            func.sum(case((age_days_expr > 14, 1), else_=0)).label("over_14_days"),
        )
        .group_by(Fab.current_stage)
        .order_by(func.count(Fab.id).desc())
    )
    if filters:
        stage_query = stage_query.where(and_(*filters))

    rows = (await db.execute(stage_query)).all()

    stage_status = [
        {
            "stage": row[0] or "unknown",
            "fab_count": row[1],
            "avg_age_days": round(_to_float(row[2]), 2),
            "max_age_days": round(_to_float(row[3]), 2),
            "stalled_over_14_days": int(row[4] or 0),
        }
        for row in rows
    ]

    return success_response(
        {
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
            "stage_status": stage_status,
        },
        "Owner shop status report generated",
    )


@router.get("/reports/owner/install-performance", response_model=SuccessResponse[dict])
async def get_owner_install_performance_report(
    start_date: Optional[date] = Query(None, description="Inclusive start date filter"),
    end_date: Optional[date] = Query(None, description="Inclusive end date filter"),
    top_n: int = Query(25, ge=1, le=100, description="Top installer rows to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Installer-focused output and labor efficiency based on completion and timer data."""
    start_dt, end_dt = _range_bounds(start_date, end_date)

    completion_filters = []
    _apply_datetime_filters(completion_filters, InstallCompletion.completion_date, start_dt, end_dt)

    completion_query = select(
        InstallCompletion.installer_id,
        InstallCompletion.fab_id,
        InstallCompletion.total_sqft_installed,
        InstallCompletion.completion_date,
    )
    if completion_filters:
        completion_query = completion_query.where(and_(*completion_filters))

    completion_rows = (await db.execute(completion_query)).all()

    by_installer: dict[int, dict] = defaultdict(lambda: {
        "completed_installs": 0,
        "sqft_installed": 0.0,
        "first_completion_at": None,
        "last_completion_at": None,
    })

    for installer_id, _fab_id, sqft_str, completed_at in completion_rows:
        stats = by_installer[installer_id]
        stats["completed_installs"] += 1
        stats["sqft_installed"] += _to_float(sqft_str)

        if completed_at is not None:
            if stats["first_completion_at"] is None or completed_at < stats["first_completion_at"]:
                stats["first_completion_at"] = completed_at
            if stats["last_completion_at"] is None or completed_at > stats["last_completion_at"]:
                stats["last_completion_at"] = completed_at

    timer_filters = []
    _apply_datetime_filters(timer_filters, InstallerJobTimerSession.session_start_at, start_dt, end_dt)
    timer_query = select(
        InstallerJobTimerSession.installer_id,
        func.sum(InstallerJobTimerSession.total_work_seconds),
        func.sum(InstallerJobTimerSession.total_pause_seconds),
    ).group_by(InstallerJobTimerSession.installer_id)
    if timer_filters:
        timer_query = timer_query.where(and_(*timer_filters))

    timer_rows = (await db.execute(timer_query)).all()

    for installer_id, work_seconds, pause_seconds in timer_rows:
        stats = by_installer[installer_id]
        stats["work_hours"] = round(_to_float(work_seconds) / 3600, 2)
        stats["pause_hours"] = round(_to_float(pause_seconds) / 3600, 2)

    installer_ids = [i for i in by_installer.keys() if i is not None]
    users_map: dict[int, str] = {}
    rates_map: dict[int, float] = {}
    if installer_ids:
        users = (
            await db.execute(
                select(User.id, User.first_name, User.last_name).where(User.id.in_(installer_ids))
            )
        ).all()
        users_map = {
            row[0]: (f"{(row[1] or '').strip()} {(row[2] or '').strip()}".strip() or f"User {row[0]}")
            for row in users
        }

        rate_rows = (
            await db.execute(
                select(
                    InstallerRateHistory.installer_id,
                    InstallerRateHistory.hourly_rate,
                    InstallerRateHistory.effective_from,
                )
                .where(
                    InstallerRateHistory.installer_id.in_(installer_ids),
                    InstallerRateHistory.is_active.is_(True),
                    or_(InstallerRateHistory.effective_to.is_(None), InstallerRateHistory.effective_to >= (start_dt or datetime.min)),
                    InstallerRateHistory.effective_from <= (end_dt or datetime.now()),
                )
                .order_by(InstallerRateHistory.installer_id, InstallerRateHistory.effective_from.desc())
            )
        ).all()

        for installer_id, hourly_rate, _effective_from in rate_rows:
            if installer_id not in rates_map:
                rates_map[installer_id] = _to_float(hourly_rate)

    installer_rows = []
    for installer_id, stats in by_installer.items():
        work_hours = _to_float(stats.get("work_hours", 0.0))
        sqft_installed = _to_float(stats.get("sqft_installed", 0.0))
        sqft_per_hour = round((sqft_installed / work_hours), 2) if work_hours else 0.0
        hourly_rate = _to_float(rates_map.get(installer_id, 0.0))
        labor_cost = round(work_hours * hourly_rate, 2)
        cost_per_sqft = round((labor_cost / sqft_installed), 2) if sqft_installed else 0.0

        installer_rows.append(
            {
                "installer_id": installer_id,
                "installer_name": users_map.get(installer_id, f"User {installer_id}" if installer_id else "Unknown"),
                "completed_installs": stats["completed_installs"],
                "sqft_installed": round(sqft_installed, 2),
                "work_hours": round(work_hours, 2),
                "pause_hours": round(_to_float(stats.get("pause_hours", 0.0)), 2),
                "sqft_per_hour": sqft_per_hour,
                "hourly_rate": round(hourly_rate, 2),
                "labor_cost": labor_cost,
                "labor_cost_per_sqft": cost_per_sqft,
                "first_completion_at": stats["first_completion_at"].isoformat() if stats.get("first_completion_at") else None,
                "last_completion_at": stats["last_completion_at"].isoformat() if stats.get("last_completion_at") else None,
            }
        )

    installer_rows.sort(key=lambda x: (x["sqft_installed"], x["completed_installs"]), reverse=True)
    installer_rows = installer_rows[:top_n]

    total_sqft_installed = round(sum(row["sqft_installed"] for row in installer_rows), 2)
    total_work_hours = round(sum(row["work_hours"] for row in installer_rows), 2)
    total_labor_cost = round(sum(row["labor_cost"] for row in installer_rows), 2)

    return success_response(
        {
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
            "summary": {
                "installer_count": len(installer_rows),
                "total_sqft_installed": total_sqft_installed,
                "total_work_hours": total_work_hours,
                "total_labor_cost": total_labor_cost,
                "portfolio_labor_cost_per_sqft": round((total_labor_cost / total_sqft_installed), 2) if total_sqft_installed else 0.0,
                "portfolio_sqft_per_hour": round((total_sqft_installed / total_work_hours), 2) if total_work_hours else 0.0,
            },
            "installer_breakdown": installer_rows,
        },
        "Owner install performance report generated",
    )


@router.get("/reports/owner/weekly-trends", response_model=SuccessResponse[dict])
async def get_owner_weekly_trends_report(
    weeks: int = Query(12, ge=4, le=52, description="How many trailing weeks to include"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Weekly trendline for owner review: new fabs, completed installs, revenue, and GP."""
    cutoff = datetime.now() - timedelta(days=weeks * 7)
    week_bucket = func.date_trunc(literal_column("'week'"), Fab.created_at)

    fab_week_rows = (
        await db.execute(
            select(
                week_bucket.label("week_start"),
                func.count(Fab.id).label("fabs_created"),
                func.sum(Fab.revenue).label("revenue"),
                func.sum(Fab.gp).label("gp"),
            )
            .where(Fab.created_at >= cutoff)
            .group_by(week_bucket)
            .order_by(week_bucket)
        )
    ).all()

    install_rows = (
        await db.execute(
            select(
                InstallCompletion.completion_date,
                InstallCompletion.total_sqft_installed,
            ).where(InstallCompletion.completion_date >= cutoff)
        )
    ).all()

    by_week: dict[str, dict] = {}

    for week_start, fabs_created, revenue, gp in fab_week_rows:
        key = week_start.date().isoformat()
        by_week[key] = {
            "week_start": key,
            "fabs_created": int(fabs_created or 0),
            "installs_completed": 0,
            "revenue": round(_to_float(revenue), 2),
            "gross_profit": round(_to_float(gp), 2),
            "sqft_installed": 0.0,
        }

    installs_by_week: dict[str, dict] = defaultdict(lambda: {"installs_completed": 0, "sqft_installed": 0.0})
    for completed_at, sqft_installed in install_rows:
        if completed_at is None:
            continue
        week_start = completed_at.date() - timedelta(days=completed_at.weekday())
        key = week_start.isoformat()
        installs_by_week[key]["installs_completed"] += 1
        installs_by_week[key]["sqft_installed"] += _to_float(sqft_installed)

    for key, values in installs_by_week.items():
        if key not in by_week:
            by_week[key] = {
                "week_start": key,
                "fabs_created": 0,
                "installs_completed": 0,
                "revenue": 0.0,
                "gross_profit": 0.0,
                "sqft_installed": 0.0,
            }
        by_week[key]["installs_completed"] = values["installs_completed"]
        by_week[key]["sqft_installed"] = round(values["sqft_installed"], 2)

    weekly_rows = [by_week[key] for key in sorted(by_week.keys())]

    return success_response(
        {
            "weeks": weeks,
            "weekly_trends": weekly_rows,
        },
        "Owner weekly trends report generated",
    )


@router.get("/reports/owner/installation-template", response_model=SuccessResponse[dict])
async def get_owner_installation_template_report(
    start_date: Optional[date] = Query(None, description="Inclusive start date filter"),
    end_date: Optional[date] = Query(None, description="Inclusive end date filter"),
    activity: str = Query("both", pattern="^(both|installation|template)$"),
    limit: int = Query(250, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Combined Installation and Template report for table-based owner view."""
    start_dt, end_dt = _range_bounds(start_date, end_date)
    rows: list[dict] = []
    installer_ids: set[int] = set()

    if activity in ("both", "installation"):
        install_filters = []
        _apply_datetime_filters(install_filters, InstallCompletion.completion_date, start_dt, end_dt)

        install_query = (
            select(
                InstallCompletion.installer_id,
                InstallCompletion.fab_id,
                InstallCompletion.total_sqft_installed,
                InstallCompletion.is_completed,
                InstallCompletion.completion_notes,
                InstallCompletion.completion_date,
                BusinessJob.name,
                BusinessJob.sq_ft,
                func.coalesce(func.sum(InstallerJobTimerSession.total_work_seconds), 0).label("work_seconds"),
            )
            .join(Fab, Fab.id == InstallCompletion.fab_id, isouter=True)
            .join(BusinessJob, BusinessJob.id == Fab.job_id, isouter=True)
            .join(
                InstallerJobTimerSession,
                and_(
                    InstallerJobTimerSession.fab_id == InstallCompletion.fab_id,
                    InstallerJobTimerSession.installer_id == InstallCompletion.installer_id,
                ),
                isouter=True,
            )
            .group_by(
                InstallCompletion.installer_id,
                InstallCompletion.fab_id,
                InstallCompletion.total_sqft_installed,
                InstallCompletion.is_completed,
                InstallCompletion.completion_notes,
                InstallCompletion.completion_date,
                BusinessJob.name,
                BusinessJob.sq_ft,
            )
            .order_by(InstallCompletion.completion_date.desc())
        )
        if install_filters:
            install_query = install_query.where(and_(*install_filters))

        install_rows = (await db.execute(install_query)).all()

        for installer_id, _fab_id, sqft_installed_raw, is_completed, completion_notes, completed_at, job_name, job_sqft, work_seconds in install_rows:
            installed_sqft = round(_to_float(sqft_installed_raw), 2)
            target_sqft = _to_float(job_sqft)
            incomplete_sqft = round(max(target_sqft - installed_sqft, 0.0), 2) if target_sqft > 0 else 0.0
            work_seconds_int = int(_to_float(work_seconds))

            if installer_id is not None:
                installer_ids.add(installer_id)

            rows.append(
                {
                    "activity_type": "Installation",
                    "activity_date": completed_at.isoformat() if completed_at else None,
                    "installer_id": installer_id,
                    "installer": None,
                    "installer_hours": round(work_seconds_int / 3600, 2),
                    "job_name": job_name or "Unknown Job",
                    "activity_complete": bool(is_completed),
                    "time_duration": _format_duration_hhmm(work_seconds_int),
                    "sq_ft_installed": installed_sqft,
                    "sq_ft_incomplete": incomplete_sqft,
                    "reason_if_not_complete": None if bool(is_completed) else (_notes_to_text(completion_notes) or "Not marked complete"),
                }
            )

    if activity in ("both", "template"):
        template_activity_date = func.coalesce(Templating.actual_end_date, Templating.actual_start_date, Templating.created_at)
        template_filters = []
        _apply_datetime_filters(template_filters, template_activity_date, start_dt, end_dt)

        template_query = (
            select(
                Templating.technician_id,
                Templating.total_sqft,
                Templating.is_completed,
                Templating.duration,
                Templating.notes,
                template_activity_date.label("activity_date"),
                BusinessJob.name,
            )
            .join(Fab, Fab.id == Templating.fab_id, isouter=True)
            .join(BusinessJob, BusinessJob.id == Fab.job_id, isouter=True)
            .order_by(template_activity_date.desc())
        )
        if template_filters:
            template_query = template_query.where(and_(*template_filters))

        template_rows = (await db.execute(template_query)).all()

        for technician_id, total_sqft_raw, is_completed, duration_minutes, notes, activity_date_value, job_name in template_rows:
            total_sqft = round(_to_float(total_sqft_raw), 2)
            is_done = bool(is_completed)
            duration_seconds = int(_to_float(duration_minutes) * 60)

            if technician_id is not None:
                installer_ids.add(technician_id)

            rows.append(
                {
                    "activity_type": "Template",
                    "activity_date": activity_date_value.isoformat() if activity_date_value else None,
                    "installer_id": technician_id,
                    "installer": None,
                    "installer_hours": round(duration_seconds / 3600, 2),
                    "job_name": job_name or "Unknown Job",
                    "activity_complete": is_done,
                    "time_duration": _format_duration_hhmm(duration_seconds),
                    "sq_ft_installed": total_sqft if is_done else 0.0,
                    "sq_ft_incomplete": 0.0 if is_done else total_sqft,
                    "reason_if_not_complete": None if is_done else (_notes_to_text(notes) or "Not marked complete"),
                }
            )

    name_map: dict[int, str] = {}
    if installer_ids:
        user_rows = (
            await db.execute(
                select(User.id, User.first_name, User.last_name).where(User.id.in_(list(installer_ids)))
            )
        ).all()
        name_map = {
            row[0]: (f"{(row[1] or '').strip()} {(row[2] or '').strip()}".strip() or f"User {row[0]}")
            for row in user_rows
        }

    for row in rows:
        installer_id = row.get("installer_id")
        row["installer"] = name_map.get(installer_id, f"User {installer_id}" if installer_id else "Unknown")

    rows.sort(key=lambda item: item.get("activity_date") or "", reverse=True)
    rows = rows[:limit]

    return success_response(
        {
            "title": "Installation and Template Report",
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
            "columns": [
                "installer",
                "installer_hours",
                "job_name",
                "activity_complete",
                "time_duration",
                "sq_ft_installed",
                "sq_ft_incomplete",
                "reason_if_not_complete",
            ],
            "summary": {
                "row_count": len(rows),
                "total_installer_hours": round(sum(_to_float(r.get("installer_hours", 0.0)) for r in rows), 2),
                "total_sq_ft_installed": round(sum(_to_float(r.get("sq_ft_installed", 0.0)) for r in rows), 2),
                "total_sq_ft_incomplete": round(sum(_to_float(r.get("sq_ft_incomplete", 0.0)) for r in rows), 2),
            },
            "rows": rows,
        },
        "Owner installation and template report generated",
    )


@router.get("/reports/owner/monthly-install-completion", response_model=SuccessResponse[dict])
async def get_owner_monthly_install_completion_report(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Monthly install completion report modeled after legacy spreadsheet format."""
    start_dt, end_dt = _month_bounds(year, month)

    query = (
        select(
            InstallCompletion.completion_date,
            Fab.fab_type,
            Fab.id,
            BusinessJob.job_number,
            Fab.no_of_pieces,
            InstallCompletion.total_sqft_installed,
            Fab.revenue,
            Fab.cost_of_stone,
            CostOfStone.total_cost,
            Fab.gp,
        )
        .join(Fab, Fab.id == InstallCompletion.fab_id)
        .join(BusinessJob, BusinessJob.id == Fab.job_id, isouter=True)
        .join(CostOfStone, CostOfStone.id == Fab.cost_of_stone_id, isouter=True)
        .where(
            InstallCompletion.is_completed.is_(True),
            InstallCompletion.completion_date >= start_dt,
            InstallCompletion.completion_date <= end_dt,
        )
        .order_by(InstallCompletion.completion_date.asc(), Fab.id.asc())
    )

    records = (await db.execute(query)).all()

    rows = []
    daily_rollup: dict[str, dict] = defaultdict(lambda: {
        "pieces": 0,
        "sq_ft": 0.0,
        "revenue": 0.0,
        "cost_of_stone": 0.0,
        "gp": 0.0,
        "row_count": 0,
    })

    for completion_date, fab_type, fab_id, job_number, pieces, sq_ft, revenue, fab_cost_of_stone, cos_total_cost, gp in records:
        sq_ft_value = round(_to_float(sq_ft), 2)
        revenue_value = round(_to_float(revenue), 2)
        cost_value = round(_to_float(fab_cost_of_stone if fab_cost_of_stone is not None else cos_total_cost), 2)
        gp_value = round(_to_float(gp), 2)
        pieces_value = int(_to_float(pieces))
        revenue_per_sqft = round((revenue_value / sq_ft_value), 2) if sq_ft_value else 0.0
        day_key = completion_date.date().isoformat()

        daily_rollup[day_key]["pieces"] += pieces_value
        daily_rollup[day_key]["sq_ft"] += sq_ft_value
        daily_rollup[day_key]["revenue"] += revenue_value
        daily_rollup[day_key]["cost_of_stone"] += cost_value
        daily_rollup[day_key]["gp"] += gp_value
        daily_rollup[day_key]["row_count"] += 1

        rows.append(
            {
                "install_date": day_key,
                "fab_type": fab_type,
                "fab_id": fab_id,
                "job_number": job_number,
                "pieces": pieces_value,
                "sq_ft": sq_ft_value,
                "revenue": revenue_value,
                "revenue_per_sq_ft": revenue_per_sqft,
                "cost_of_stone": cost_value,
                "gp": gp_value,
            }
        )

    daily_totals = []
    for day_key in sorted(daily_rollup.keys()):
        item = daily_rollup[day_key]
        day_sqft = round(item["sq_ft"], 2)
        day_revenue = round(item["revenue"], 2)
        daily_totals.append(
            {
                "install_date": day_key,
                "pieces": int(item["pieces"]),
                "sq_ft": day_sqft,
                "revenue": day_revenue,
                "revenue_per_sq_ft": round((day_revenue / day_sqft), 2) if day_sqft else 0.0,
                "cost_of_stone": round(item["cost_of_stone"], 2),
                "gp": round(item["gp"], 2),
                "row_count": int(item["row_count"]),
            }
        )

    total_sqft = round(sum(item["sq_ft"] for item in daily_rollup.values()), 2)
    total_revenue = round(sum(item["revenue"] for item in daily_rollup.values()), 2)
    total_cost = round(sum(item["cost_of_stone"] for item in daily_rollup.values()), 2)
    total_gp = round(sum(item["gp"] for item in daily_rollup.values()), 2)

    return success_response(
        {
            "title": "Monthly Install Completion",
            "year": year,
            "month": month,
            "columns": [
                "install_date",
                "fab_type",
                "fab_id",
                "job_number",
                "pieces",
                "sq_ft",
                "revenue",
                "revenue_per_sq_ft",
                "cost_of_stone",
                "gp",
            ],
            "summary": {
                "pieces": int(sum(item["pieces"] for item in daily_rollup.values())),
                "sq_ft": total_sqft,
                "revenue": total_revenue,
                "revenue_per_sq_ft": round((total_revenue / total_sqft), 2) if total_sqft else 0.0,
                "cost_of_stone": total_cost,
                "gp": total_gp,
                "row_count": len(rows),
            },
            "daily_totals": daily_totals,
            "rows": rows,
        },
        "Owner monthly install completion report generated",
    )


@router.get("/reports/owner/daily-install-completion", response_model=SuccessResponse[dict])
async def get_owner_daily_install_completion_report(
    start_date: Optional[date] = Query(None, description="Inclusive start date filter"),
    end_date: Optional[date] = Query(None, description="Inclusive end date filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Daily install completion report across a date range, grouped by install date."""
    if start_date is None and end_date is None:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
    elif start_date is None and end_date is not None:
        start_date = end_date
    elif start_date is not None and end_date is None:
        end_date = start_date

    start_dt, end_dt = _range_bounds(start_date, end_date)

    query = (
        select(
            InstallCompletion.completion_date,
            Fab.fab_type,
            Fab.id,
            BusinessJob.job_number,
            Fab.no_of_pieces,
            InstallCompletion.total_sqft_installed,
            Fab.revenue,
            Fab.cost_of_stone,
            CostOfStone.total_cost,
            Fab.gp,
        )
        .join(Fab, Fab.id == InstallCompletion.fab_id)
        .join(BusinessJob, BusinessJob.id == Fab.job_id, isouter=True)
        .join(CostOfStone, CostOfStone.id == Fab.cost_of_stone_id, isouter=True)
        .where(InstallCompletion.completion_date >= start_dt, InstallCompletion.completion_date <= end_dt)
        .order_by(InstallCompletion.completion_date.asc(), Fab.id.asc())
    )

    records = (await db.execute(query)).all()

    rows = []
    daily_rollup: dict[str, dict] = defaultdict(lambda: {
        "pieces": 0,
        "sq_ft": 0.0,
        "revenue": 0.0,
        "cost_of_stone": 0.0,
        "gp": 0.0,
        "row_count": 0,
    })

    for completion_date, fab_type, fab_id, job_number, pieces, sq_ft, revenue, fab_cost_of_stone, cos_total_cost, gp in records:
        sq_ft_value = round(_to_float(sq_ft), 2)
        revenue_value = round(_to_float(revenue), 2)
        cost_value = round(_to_float(fab_cost_of_stone if fab_cost_of_stone is not None else cos_total_cost), 2)
        gp_value = round(_to_float(gp), 2)
        pieces_value = int(_to_float(pieces))
        revenue_per_sqft = round((revenue_value / sq_ft_value), 2) if sq_ft_value else 0.0
        day_key = completion_date.date().isoformat()

        daily_rollup[day_key]["pieces"] += pieces_value
        daily_rollup[day_key]["sq_ft"] += sq_ft_value
        daily_rollup[day_key]["revenue"] += revenue_value
        daily_rollup[day_key]["cost_of_stone"] += cost_value
        daily_rollup[day_key]["gp"] += gp_value
        daily_rollup[day_key]["row_count"] += 1

        rows.append(
            {
                "install_date": day_key,
                "fab_type": fab_type,
                "fab_id": fab_id,
                "job_number": job_number,
                "pieces": pieces_value,
                "sq_ft": sq_ft_value,
                "revenue": revenue_value,
                "revenue_per_sq_ft": revenue_per_sqft,
                "cost_of_stone": cost_value,
                "gp": gp_value,
            }
        )

    daily_totals = []
    for day_key in sorted(daily_rollup.keys()):
        item = daily_rollup[day_key]
        day_sqft = round(item["sq_ft"], 2)
        day_revenue = round(item["revenue"], 2)
        daily_totals.append(
            {
                "install_date": day_key,
                "pieces": int(item["pieces"]),
                "sq_ft": day_sqft,
                "revenue": day_revenue,
                "revenue_per_sq_ft": round((day_revenue / day_sqft), 2) if day_sqft else 0.0,
                "cost_of_stone": round(item["cost_of_stone"], 2),
                "gp": round(item["gp"], 2),
                "row_count": int(item["row_count"]),
            }
        )

    total_sqft = round(sum(item["sq_ft"] for item in daily_rollup.values()), 2)
    total_revenue = round(sum(item["revenue"] for item in daily_rollup.values()), 2)
    total_cost = round(sum(item["cost_of_stone"] for item in daily_rollup.values()), 2)
    total_gp = round(sum(item["gp"] for item in daily_rollup.values()), 2)

    return success_response(
        {
            "title": "Daily Install Completion",
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
            "columns": [
                "install_date",
                "fab_type",
                "fab_id",
                "job_number",
                "pieces",
                "sq_ft",
                "revenue",
                "revenue_per_sq_ft",
                "cost_of_stone",
                "gp",
            ],
            "summary": {
                "pieces": int(sum(item["pieces"] for item in daily_rollup.values())),
                "sq_ft": total_sqft,
                "revenue": total_revenue,
                "revenue_per_sq_ft": round((total_revenue / total_sqft), 2) if total_sqft else 0.0,
                "cost_of_stone": total_cost,
                "gp": total_gp,
                "row_count": len(rows),
            },
            "daily_totals": daily_totals,
            "rows": rows,
        },
        "Owner daily install completion report generated",
    )


@router.get("/reports/owner/monthly-cut-completion", response_model=SuccessResponse[dict])
async def get_owner_monthly_cut_completion_report(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Monthly cut completion report modeled after legacy spreadsheet format."""
    start_dt, end_dt = _month_bounds(year, month)
    cut_date_expr = func.coalesce(Fab.shop_date_schedule, Fab.final_programming_completed_date)

    query = (
        select(
            cut_date_expr.label("cut_date"),
            Fab.fab_type,
            Fab.id,
            BusinessJob.job_number,
            Fab.no_of_pieces,
            Fab.total_sqft,
            Fab.revenue,
            Fab.cost_of_stone,
            CostOfStone.total_cost,
            Fab.gp,
        )
        .join(BusinessJob, BusinessJob.id == Fab.job_id, isouter=True)
        .join(CostOfStone, CostOfStone.id == Fab.cost_of_stone_id, isouter=True)
        .join(CutList, CutList.fab_id == Fab.id, isouter=True)
        .where(cut_date_expr >= start_dt, cut_date_expr <= end_dt)
        .order_by(cut_date_expr.asc(), Fab.id.asc())
    )

    records = (await db.execute(query)).all()

    rows = []
    daily_rollup: dict[str, dict] = defaultdict(lambda: {
        "pieces": 0,
        "sq_ft": 0.0,
        "revenue": 0.0,
        "cost_of_stone": 0.0,
        "gp": 0.0,
        "row_count": 0,
    })

    for cut_date, fab_type, fab_id, job_number, pieces, sq_ft, revenue, fab_cost_of_stone, cos_total_cost, gp in records:
        if cut_date is None:
            continue

        sq_ft_value = round(_to_float(sq_ft), 2)
        revenue_value = round(_to_float(revenue), 2)
        cost_value = round(_to_float(fab_cost_of_stone if fab_cost_of_stone is not None else cos_total_cost), 2)
        gp_value = round(_to_float(gp), 2)
        pieces_value = int(_to_float(pieces))
        revenue_per_sqft = round((revenue_value / sq_ft_value), 2) if sq_ft_value else 0.0
        day_key = cut_date.date().isoformat()

        daily_rollup[day_key]["pieces"] += pieces_value
        daily_rollup[day_key]["sq_ft"] += sq_ft_value
        daily_rollup[day_key]["revenue"] += revenue_value
        daily_rollup[day_key]["cost_of_stone"] += cost_value
        daily_rollup[day_key]["gp"] += gp_value
        daily_rollup[day_key]["row_count"] += 1

        rows.append(
            {
                "cut_date": day_key,
                "fab_type": fab_type,
                "fab_id": fab_id,
                "job_number": job_number,
                "pieces": pieces_value,
                "sq_ft": sq_ft_value,
                "revenue": revenue_value,
                "revenue_per_sq_ft": revenue_per_sqft,
                "cost_of_stone": cost_value,
                "gp": gp_value,
            }
        )

    daily_totals = []
    for day_key in sorted(daily_rollup.keys()):
        item = daily_rollup[day_key]
        day_sqft = round(item["sq_ft"], 2)
        day_revenue = round(item["revenue"], 2)
        daily_totals.append(
            {
                "cut_date": day_key,
                "pieces": int(item["pieces"]),
                "sq_ft": day_sqft,
                "revenue": day_revenue,
                "revenue_per_sq_ft": round((day_revenue / day_sqft), 2) if day_sqft else 0.0,
                "cost_of_stone": round(item["cost_of_stone"], 2),
                "gp": round(item["gp"], 2),
                "row_count": int(item["row_count"]),
            }
        )

    total_sqft = round(sum(item["sq_ft"] for item in daily_rollup.values()), 2)
    total_revenue = round(sum(item["revenue"] for item in daily_rollup.values()), 2)
    total_cost = round(sum(item["cost_of_stone"] for item in daily_rollup.values()), 2)
    total_gp = round(sum(item["gp"] for item in daily_rollup.values()), 2)

    return success_response(
        {
            "title": "Monthly Cut Completion",
            "year": year,
            "month": month,
            "columns": [
                "cut_date",
                "fab_type",
                "fab_id",
                "job_number",
                "pieces",
                "sq_ft",
                "revenue",
                "revenue_per_sq_ft",
                "cost_of_stone",
                "gp",
            ],
            "summary": {
                "pieces": int(sum(item["pieces"] for item in daily_rollup.values())),
                "sq_ft": total_sqft,
                "revenue": total_revenue,
                "revenue_per_sq_ft": round((total_revenue / total_sqft), 2) if total_sqft else 0.0,
                "cost_of_stone": total_cost,
                "gp": total_gp,
                "row_count": len(rows),
            },
            "daily_totals": daily_totals,
            "rows": rows,
        },
        "Owner monthly cut completion report generated",
    )


@router.get("/reports/daily-install-completion", response_model=SuccessResponse[dict])
async def get_daily_install_completion_report(
    start_date: Optional[date] = Query(None, description="Inclusive start date filter"),
    end_date: Optional[date] = Query(None, description="Inclusive end date filter"),
    job_number: Optional[str] = Query(None, description="Optional job number filter"),
    fab_id: Optional[int] = Query(None, gt=0, description="Optional FAB ID filter"),
    installer_id: Optional[int] = Query(None, gt=0, description="Optional installer user ID filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Daily install completion report with optional filters and daily/grand totals."""
    start_dt, end_dt = _range_bounds(start_date, end_date)

    query = (
        select(
            InstallCompletion.completion_date,
            Fab.id,
            Fab.fab_type,
            BusinessJob.job_number,
            BusinessJob.name,
            InstallCompletion.installer_id,
            User.first_name,
            User.last_name,
            InstallCompletion.total_sqft_installed,
            Fab.revenue,
            Fab.gp,
        )
        .select_from(InstallCompletion)
        .join(Fab, Fab.id == InstallCompletion.fab_id)
        .join(BusinessJob, BusinessJob.id == Fab.job_id, isouter=True)
        .join(User, User.id == InstallCompletion.installer_id, isouter=True)
        .where(Fab.current_stage == "install_completion")
        .order_by(InstallCompletion.completion_date.asc(), Fab.id.asc())
    )

    if start_dt is not None:
        query = query.where(InstallCompletion.completion_date >= start_dt)
    if end_dt is not None:
        query = query.where(InstallCompletion.completion_date <= end_dt)
    if job_number:
        query = query.where(BusinessJob.job_number.ilike(f"%{job_number.strip()}%"))
    if fab_id is not None:
        query = query.where(Fab.id == fab_id)
    if installer_id is not None:
        query = query.where(InstallCompletion.installer_id == installer_id)

    records = (await db.execute(query)).all()

    entries = []
    daily_totals_map: dict[str, dict] = defaultdict(lambda: {
        "total_sqft": 0.0,
        "total_revenue": 0.0,
        "total_gp": 0.0,
        "count": 0,
    })

    grand_total_sqft = 0.0
    grand_total_revenue = 0.0
    grand_total_gp = 0.0

    for (
        completion_date,
        row_fab_id,
        row_fab_type,
        row_job_number,
        row_job_name,
        row_installer_id,
        installer_first_name,
        installer_last_name,
        sqft_installed_raw,
        revenue_raw,
        gp_raw,
    ) in records:
        if completion_date is None:
            continue

        day_key = completion_date.date().isoformat()
        sqft_value = round(_to_float(sqft_installed_raw), 2)
        revenue_value = round(_to_float(revenue_raw), 2)
        gp_value = round(_to_float(gp_raw), 2)

        daily_totals_map[day_key]["total_sqft"] += sqft_value
        daily_totals_map[day_key]["total_revenue"] += revenue_value
        daily_totals_map[day_key]["total_gp"] += gp_value
        daily_totals_map[day_key]["count"] += 1

        grand_total_sqft += sqft_value
        grand_total_revenue += revenue_value
        grand_total_gp += gp_value

        installer_name = (f"{(installer_first_name or '').strip()} {(installer_last_name or '').strip()}".strip() or None)
        entries.append(
            {
                "install_date": day_key,
                "fab_id": row_fab_id,
                "fab_type": row_fab_type,
                "job_number": row_job_number,
                "job_name": row_job_name,
                "installer_id": row_installer_id,
                "installer_name": installer_name,
                "sqft": sqft_value,
                "revenue": revenue_value,
                "gp": gp_value,
            }
        )

    daily_totals = []
    for day_key in sorted(daily_totals_map.keys()):
        item = daily_totals_map[day_key]
        daily_totals.append(
            {
                "install_date": day_key,
                "total_sqft": round(item["total_sqft"], 2),
                "total_revenue": round(item["total_revenue"], 2),
                "total_gp": round(item["total_gp"], 2),
                "entry_count": int(item["count"]),
            }
        )

    return success_response(
        {
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
            "filters": {
                "job_number": job_number,
                "fab_id": fab_id,
                "installer_id": installer_id,
            },
            "grand_totals": {
                "total_sqft": round(grand_total_sqft, 2),
                "total_revenue": round(grand_total_revenue, 2),
                "total_gp": round(grand_total_gp, 2),
                "entry_count": len(entries),
            },
            "daily_totals": daily_totals,
            "entries": entries,
        },
        "Daily Install Completion data retrieved successfully",
    )


@router.get("/reports/monthly-cut-completion", response_model=SuccessResponse[dict])
async def get_monthly_cut_completion_report(
    month: str = Query(..., description="Month number (1-12) or month name (e.g. April)"),
    year: int = Query(..., ge=2000, le=2100),
    fab_type: Optional[str] = Query(None, description="Optional FAB type filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Monthly cut completion report with summary and detailed entries."""
    month_num = _parse_month_input(month)
    if month_num is None:
        return success_response(None, "Invalid month. Use month number (1-12) or month name", status_code=400)

    start_dt, end_dt = _month_bounds(year, month_num)
    cut_date_expr = func.coalesce(Fab.shop_date_schedule, Fab.final_programming_completed_date)

    query = (
        select(
            cut_date_expr.label("cut_date"),
            Fab.fab_type,
            Fab.id,
            BusinessJob.job_number,
            Account.name.label("account_name"),
            StoneType.name.label("stone_type_name"),
            StoneColor.name.label("stone_color_name"),
            StoneThickness.thickness.label("stone_thickness"),
            Fab.no_of_pieces,
            Fab.total_sqft,
            CostOfStone.cost_per_sqft,
            Fab.revenue,
            Fab.cost_of_stone,
            CostOfStone.total_cost,
            Fab.gp,
        )
        .join(BusinessJob, BusinessJob.id == Fab.job_id, isouter=True)
        .join(Account, Account.id == BusinessJob.account_id, isouter=True)
        .join(StoneType, StoneType.id == Fab.stone_type_id, isouter=True)
        .join(StoneColor, StoneColor.id == Fab.stone_color_id, isouter=True)
        .join(StoneThickness, StoneThickness.id == Fab.stone_thickness_id, isouter=True)
        .join(CostOfStone, CostOfStone.id == Fab.cost_of_stone_id, isouter=True)
        .where(cut_date_expr >= start_dt, cut_date_expr <= end_dt)
        .order_by(cut_date_expr.asc(), Fab.id.asc())
    )

    if fab_type:
        query = query.where(func.lower(Fab.fab_type) == fab_type.strip().lower())

    records = (await db.execute(query)).all()

    entries = []
    total_pieces = 0
    total_sqft = 0.0
    total_revenue = 0.0
    total_cost_of_stone = 0.0
    total_gp = 0.0

    for (
        cut_date,
        row_fab_type,
        fab_id,
        job_number,
        account_name,
        stone_type_name,
        stone_color_name,
        stone_thickness,
        no_of_pieces,
        sqft,
        cost_per_sqft_raw,
        revenue_raw,
        fab_cost_of_stone,
        cos_total_cost,
        gp_raw,
    ) in records:
        if cut_date is None:
            continue

        pieces_value = int(_to_float(no_of_pieces))
        sqft_value = round(_to_float(sqft), 2)
        cost_per_sf = round(_to_float(cost_per_sqft_raw), 2)
        revenue_value = round(_to_float(revenue_raw), 2)
        cost_of_stone_value = round(_to_float(fab_cost_of_stone if fab_cost_of_stone is not None else cos_total_cost), 2)
        gp_value = round(_to_float(gp_raw), 2)
        if gp_raw is None:
            gp_value = round(revenue_value - cost_of_stone_value, 2)

        total_pieces += pieces_value
        total_sqft += sqft_value
        total_revenue += revenue_value
        total_cost_of_stone += cost_of_stone_value
        total_gp += gp_value

        info_parts = [account_name, stone_type_name, stone_color_name, stone_thickness]
        fab_info = " - ".join(str(part).strip() for part in info_parts if part and str(part).strip())

        entries.append(
            {
                "cut_date": cut_date.date().isoformat(),
                "fab_type": row_fab_type,
                "fab_id": fab_id,
                "job_number": job_number,
                "fab_info": fab_info or None,
                "no_of_pieces": pieces_value,
                "sqft": sqft_value,
                "cost/sf": cost_per_sf,
                "revenue": revenue_value,
                "revenue_per_sqft": round((revenue_value / sqft_value), 2) if sqft_value else 0.0,
                "cost_of_stone": cost_of_stone_value,
                "gp": gp_value,
            }
        )

    total_sqft = round(total_sqft, 2)
    total_revenue = round(total_revenue, 2)
    total_cost_of_stone = round(total_cost_of_stone, 2)
    total_gp = round(total_gp, 2)

    return success_response(
        {
            "month": calendar.month_name[month_num],
            "year": year,
            "summary": {
                "total_no_of_pieces": int(total_pieces),
                "total_sqft": total_sqft,
                "total_revenue": total_revenue,
                "total_revenue/sqft": round((total_revenue / total_sqft), 2) if total_sqft else 0.0,
                "total_cost_of_stone": total_cost_of_stone,
                "total_gp": total_gp,
            },
            "entries": entries,
        },
        "Monthly Cut Completion data retrieved successfully",
    )


@router.get("/reports/owner/turnaround-times", response_model=SuccessResponse[dict])
async def get_owner_turnaround_times_report(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    limit: int = Query(2000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Turnaround-times report aligned to template/predraft/draft/sct/final-prog/cut/fab-complete milestones."""
    start_dt, end_dt = _month_bounds(year, month)

    install_subquery = (
        select(
            InstallCompletion.fab_id.label("fab_id"),
            func.max(InstallCompletion.completion_date).label("fab_complete_date"),
        )
        .group_by(InstallCompletion.fab_id)
        .subquery()
    )

    query = (
        select(
            Fab.id,
            BusinessJob.job_number,
            Fab.no_of_pieces,
            Fab.total_sqft,
            Fab.template_completed_date,
            Fab.predraft_completed_date,
            Fab.draft_completed_date,
            func.coalesce(Fab.sales_ct_completed_date, Fab.sct_completed_date).label("sct_date"),
            Fab.final_programming_completed_date,
            Fab.shop_date_schedule,
            install_subquery.c.fab_complete_date,
        )
        .join(BusinessJob, BusinessJob.id == Fab.job_id, isouter=True)
        .join(install_subquery, install_subquery.c.fab_id == Fab.id, isouter=True)
        .where(
            install_subquery.c.fab_complete_date.is_not(None),
            install_subquery.c.fab_complete_date >= start_dt,
            install_subquery.c.fab_complete_date <= end_dt,
        )
        .order_by(install_subquery.c.fab_complete_date.desc(), Fab.id.asc())
        .limit(limit)
    )

    records = (await db.execute(query)).all()
    rows = []

    pd_days_values: list[int] = []
    draft_days_values: list[int] = []
    sct_days_values: list[int] = []
    fp_days_values: list[int] = []
    cut_days_values: list[int] = []
    fab_days_values: list[int] = []
    total_days_values: list[int] = []

    for (
        fab_id,
        job_number,
        pieces,
        total_sqft,
        template_date,
        predraft_date,
        draft_date,
        sct_date,
        final_prog_date,
        cut_date,
        fab_complete_date,
    ) in records:
        predraft_days = _days_between(template_date, predraft_date)
        draft_days = _days_between(predraft_date or template_date, draft_date)
        sct_days = _days_between(draft_date, sct_date)
        final_prog_days = _days_between(sct_date, final_prog_date)
        cut_days = _days_between(final_prog_date, cut_date)
        fab_days = _days_between(cut_date, fab_complete_date)
        total_days = _days_between(template_date, fab_complete_date)

        if predraft_days is not None:
            pd_days_values.append(predraft_days)
        if draft_days is not None:
            draft_days_values.append(draft_days)
        if sct_days is not None:
            sct_days_values.append(sct_days)
        if final_prog_days is not None:
            fp_days_values.append(final_prog_days)
        if cut_days is not None:
            cut_days_values.append(cut_days)
        if fab_days is not None:
            fab_days_values.append(fab_days)
        if total_days is not None:
            total_days_values.append(total_days)

        rows.append(
            {
                "fab_id": fab_id,
                "job_number": job_number,
                "pieces": int(_to_float(pieces)),
                "total_sq_ft": round(_to_float(total_sqft), 2),
                "template_date": template_date.isoformat() if template_date else None,
                "predraft_date": predraft_date.isoformat() if predraft_date else None,
                "predraft_days": predraft_days,
                "draft_date": draft_date.isoformat() if draft_date else None,
                "draft_days": draft_days,
                "sct_date": sct_date.isoformat() if sct_date else None,
                "sct_days": sct_days,
                "final_prog_date": final_prog_date.isoformat() if final_prog_date else None,
                "final_prog_days": final_prog_days,
                "cut_date": cut_date.isoformat() if cut_date else None,
                "cut_days": cut_days,
                "fab_complete_date": fab_complete_date.isoformat() if fab_complete_date else None,
                "fab_days": fab_days,
                "total_days": total_days,
            }
        )

    def _stats(values: list[int]) -> dict:
        if not values:
            return {"min": None, "max": None, "avg": None}
        return {
            "min": min(values),
            "max": max(values),
            "avg": round(sum(values) / len(values), 2),
        }

    return success_response(
        {
            "title": "Turnaround Times Report",
            "year": year,
            "month": month,
            "summary": {
                "predraft_days": _stats(pd_days_values),
                "draft_days": _stats(draft_days_values),
                "sct_days": _stats(sct_days_values),
                "final_prog_days": _stats(fp_days_values),
                "cut_days": _stats(cut_days_values),
                "fab_days": _stats(fab_days_values),
                "total_days": _stats(total_days_values),
                "row_count": len(rows),
            },
            "rows": rows,
        },
        "Owner turnaround times report generated",
    )


@router.get("/reports/owner/service-level", response_model=SuccessResponse[dict])
async def get_owner_service_level_report(
    start_date: Optional[date] = Query(None, description="Inclusive start date filter"),
    end_date: Optional[date] = Query(None, description="Inclusive end date filter"),
    date_basis: str = Query("completed", pattern="^(created|scheduled|completed)$"),
    sla_days: int = Query(14, ge=1, le=365, description="SLA threshold in days"),
    breach_limit: int = Query(500, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Service-level report with KPI widgets, stage heat map, and Fab-level bottleneck rows."""
    start_dt, end_dt = _range_bounds(start_date, end_date)

    stage_target_days = {
        "Pre-Draft Review": 2.0,
        "Drafting": 3.0,
        "SCT": 3.0,
        "SlabSmith": 2.0,
        "Final Programming": 2.0,
        "CNC": 1.0,
    }
    revision_target_days = {
        "cad": 1.0,
        "template": 1.0,
        "sales": 1.0,
        "client": 2.0,
    }

    def _revision_subtype(value: Optional[str]) -> Optional[str]:
        text = (value or "").strip().lower()
        if not text:
            return None
        if "cad" in text:
            return "cad"
        if "template" in text:
            return "template"
        if "sales" in text:
            return "sales"
        if "client" in text:
            return "client"
        return None

    def _target_days_for(stage_name: str, revision_type: Optional[str]) -> float:
        if stage_name == "Revisions":
            revision_key = _revision_subtype(revision_type)
            if revision_key is not None:
                return revision_target_days[revision_key]
            return float(sla_days)
        return float(stage_target_days.get(stage_name, float(sla_days)))

    def _risk_color(age_days: float, target_days: float) -> str:
        yellow_threshold = max(target_days * 0.75, 0.0)
        if age_days > target_days:
            return "red"
        if age_days >= yellow_threshold:
            return "yellow"
        return "green"

    def _normalize_stage(stage_value: Optional[str]) -> str:
        stage = (stage_value or "").strip().lower()
        if "pre_draft" in stage or "predraft" in stage:
            return "Pre-Draft Review"
        if "revision" in stage:
            return "Revisions"
        if stage in {"sct", "sales_ct"} or "sales_ct" in stage or "salesct" in stage:
            return "SCT"
        if "slabsmith" in stage or "slab_smith" in stage:
            return "SlabSmith"
        if "final_program" in stage:
            return "Final Programming"
        if "cnc" in stage:
            return "CNC"
        if "draft" in stage:
            return "Drafting"
        return "Other"

    completion_query = (
        select(
            Fab.id.label("fab_id"),
            BusinessJob.job_number,
            Fab.created_at,
            Fab.template_completed_date,
            InstallCompletion.install_date,
            InstallCompletion.completion_date,
            Fab.shop_date_schedule,
            Fab.shop_est_completion_date,
            Fab.installation_date,
            InstallCompletion.installer_id,
            InstallCompletion.total_sqft_installed,
        )
        .select_from(InstallCompletion)
        .join(Fab, Fab.id == InstallCompletion.fab_id)
        .join(BusinessJob, BusinessJob.id == Fab.job_id, isouter=True)
    )

    if date_basis == "created":
        if start_dt is not None:
            completion_query = completion_query.where(Fab.created_at >= start_dt)
        if end_dt is not None:
            completion_query = completion_query.where(Fab.created_at <= end_dt)
    elif date_basis == "scheduled":
        scheduled_basis = func.coalesce(
            InstallCompletion.install_date,
            Fab.installation_date,
            Fab.shop_est_completion_date,
            Fab.shop_date_schedule,
        )
        if start_dt is not None:
            completion_query = completion_query.where(scheduled_basis >= start_dt)
        if end_dt is not None:
            completion_query = completion_query.where(scheduled_basis <= end_dt)
    else:
        if start_dt is not None:
            completion_query = completion_query.where(InstallCompletion.completion_date >= start_dt)
        if end_dt is not None:
            completion_query = completion_query.where(InstallCompletion.completion_date <= end_dt)

    completion_rows = (await db.execute(completion_query)).all()

    total_completed = len(completion_rows)
    on_time_eligible = 0
    on_time_count = 0
    cycle_days: list[int] = []
    cycle_rows = []

    for (
        fab_id,
        job_number,
        created_at,
        template_completed_at,
        install_date,
        completion_date,
        shop_date_schedule,
        shop_est_completion_date,
        installation_date,
        installer_id,
        total_sqft_installed,
    ) in completion_rows:
        due_date = install_date or installation_date or shop_est_completion_date or shop_date_schedule
        if due_date is not None:
            on_time_eligible += 1
            if completion_date is not None and completion_date <= due_date:
                on_time_count += 1

        cycle_day = _days_between(template_completed_at, completion_date)
        if cycle_day is not None:
            cycle_days.append(cycle_day)

        cycle_rows.append(
            {
                "fab_id": fab_id,
                "job_number": job_number,
                "installer_id": installer_id,
                "created_at": created_at.isoformat() if created_at else None,
                "template_completed_at": template_completed_at.isoformat() if template_completed_at else None,
                "due_date": due_date.isoformat() if due_date else None,
                "completion_date": completion_date.isoformat() if completion_date else None,
                "cycle_days": cycle_day,
                "is_on_time": bool(due_date is not None and completion_date is not None and completion_date <= due_date),
                "total_sqft_installed": round(_to_float(total_sqft_installed), 2),
            }
        )

    cycle_stats = {
        "count": len(cycle_days),
        "min_days": min(cycle_days) if cycle_days else None,
        "max_days": max(cycle_days) if cycle_days else None,
        "avg_days": round(sum(cycle_days) / len(cycle_days), 2) if cycle_days else None,
    }

    completed_subquery = (
        select(
            InstallCompletion.fab_id.label("fab_id"),
            func.max(InstallCompletion.completion_date).label("completion_date"),
        )
        .group_by(InstallCompletion.fab_id)
        .subquery()
    )

    schedule_subquery = (
        select(
            InstallScheduling.fab_id.label("fab_id"),
            func.max(InstallScheduling.scheduled_install_date).label("scheduled_install_date"),
        )
        .group_by(InstallScheduling.fab_id)
        .subquery()
    )

    revision_subquery = (
        select(
            Revision.fab_id.label("fab_id"),
            Revision.revision_type,
            Revision.assigned_to,
            Revision.actual_start_date,
            Revision.scheduled_start_date,
            Revision.created_at,
        )
        .subquery()
    )

    backlog_query = (
        select(
            Fab.id,
            BusinessJob.job_number,
            BusinessJob.name,
            BusinessJob.priority,
            Fab.current_stage,
            Fab.fab_type,
            Fab.total_sqft,
            Fab.no_of_pieces,
            Fab.created_at,
            Fab.updated_at,
            Fab.template_completed_date,
            Fab.predraft_completed_date,
            Fab.draft_completed_date,
            Fab.slabsmith_completed_date,
            Fab.sales_ct_completed_date,
            Fab.sct_completed_date,
            Fab.final_programming_completed_date,
            Fab.installation_date,
            Fab.shop_est_completion_date,
            Fab.shop_date_schedule,
            Fab.status_id,
            Fab.drafter_id,
            Fab.sales_person_id,
            schedule_subquery.c.scheduled_install_date,
            completed_subquery.c.completion_date,
            revision_subquery.c.revision_type,
            revision_subquery.c.assigned_to,
            revision_subquery.c.actual_start_date,
            revision_subquery.c.scheduled_start_date,
            revision_subquery.c.created_at,
        )
        .select_from(Fab)
        .join(BusinessJob, BusinessJob.id == Fab.job_id, isouter=True)
        .join(schedule_subquery, schedule_subquery.c.fab_id == Fab.id, isouter=True)
        .join(completed_subquery, completed_subquery.c.fab_id == Fab.id, isouter=True)
        .join(revision_subquery, revision_subquery.c.fab_id == Fab.id, isouter=True)
        .where(completed_subquery.c.completion_date.is_(None), Fab.status_id == 1)
    )

    if date_basis == "created":
        if start_dt is not None:
            backlog_query = backlog_query.where(Fab.created_at >= start_dt)
        if end_dt is not None:
            backlog_query = backlog_query.where(Fab.created_at <= end_dt)
    elif date_basis == "scheduled":
        scheduled_backlog_basis = func.coalesce(
            schedule_subquery.c.scheduled_install_date,
            Fab.installation_date,
            Fab.shop_est_completion_date,
            Fab.shop_date_schedule,
        )
        if start_dt is not None:
            backlog_query = backlog_query.where(scheduled_backlog_basis >= start_dt)
        if end_dt is not None:
            backlog_query = backlog_query.where(scheduled_backlog_basis <= end_dt)

    backlog_rows = (await db.execute(backlog_query)).all()

    bucket_totals = {
        "0_7_days": 0,
        "8_14_days": 0,
        "15_30_days": 0,
        "31_plus_days": 0,
    }

    stage_display_names = [
        "Pre-Draft Review",
        "Drafting",
        "Revisions",
        "SCT",
        "SlabSmith",
        "Final Programming",
        "CNC",
    ]
    stage_rollup: dict[str, dict] = {
        stage_name: {
            "green": 0,
            "yellow": 0,
            "red": 0,
            "total_wip": 0,
            "total_age_days": 0,
        }
        for stage_name in stage_display_names
    }

    total_green = 0
    total_yellow = 0
    total_red = 0
    oldest_open_job = None
    breach_details = []
    fab_status_rows = []

    def _first_name(names: dict[int, str], user_id: Optional[int]) -> Optional[str]:
        if user_id is None:
            return None
        return names.get(user_id)

    backlog_records = backlog_rows
    user_ids: set[int] = set()
    for row in backlog_records:
        drafter_id = row[21]
        sales_person_id = row[22]
        revision_assigned_to = row[26]
        if drafter_id is not None:
            user_ids.add(drafter_id)
        if sales_person_id is not None:
            user_ids.add(sales_person_id)
        if revision_assigned_to is not None:
            user_ids.add(revision_assigned_to)

    user_names: dict[int, str] = {}
    if user_ids:
        user_rows = (
            await db.execute(
                select(User.id, User.first_name, User.last_name).where(User.id.in_(list(user_ids)))
            )
        ).all()
        user_names = {
            user_id: (f"{(first_name or '').strip()} {(last_name or '').strip()}".strip() or f"User {user_id}")
            for user_id, first_name, last_name in user_rows
        }

    now_dt = datetime.now()
    for (
        fab_id,
        job_number,
        job_name,
        job_priority,
        current_stage,
        fab_type,
        total_sqft,
        no_of_pieces,
        created_at,
        updated_at,
        template_completed_at,
        predraft_completed_at,
        draft_completed_at,
        slabsmith_completed_at,
        sales_ct_completed_at,
        sct_completed_at,
        final_programming_completed_at,
        installation_date,
        shop_est_completion_date,
        shop_date_schedule,
        _status_id,
        drafter_id,
        sales_person_id,
        scheduled_install_date,
        _completion_date,
        revision_type,
        revision_assigned_to,
        revision_actual_start,
        revision_scheduled_start,
        revision_created_at,
    ) in backlog_rows:
        due_date = scheduled_install_date or installation_date or shop_est_completion_date or shop_date_schedule
        cycle_anchor = template_completed_at or created_at
        stage_name = _normalize_stage(current_stage)

        if stage_name == "Pre-Draft Review":
            stage_anchor = template_completed_at or created_at
        elif stage_name == "Drafting":
            stage_anchor = predraft_completed_at or template_completed_at or created_at
        elif stage_name == "Revisions":
            stage_anchor = revision_actual_start or revision_scheduled_start or revision_created_at or updated_at or created_at
        elif stage_name == "SCT":
            stage_anchor = draft_completed_at or updated_at or created_at
        elif stage_name == "SlabSmith":
            stage_anchor = sales_ct_completed_at or sct_completed_at or updated_at or created_at
        elif stage_name == "Final Programming":
            stage_anchor = slabsmith_completed_at or sales_ct_completed_at or sct_completed_at or updated_at or created_at
        elif stage_name == "CNC":
            stage_anchor = final_programming_completed_at or updated_at or created_at
        else:
            stage_anchor = updated_at or created_at

        if stage_anchor is None:
            continue

        days_since_template = _days_between(template_completed_at, now_dt)
        days_in_stage = max((now_dt.date() - stage_anchor.date()).days, 0)
        target_days = _target_days_for(stage_name, revision_type)
        risk_color = _risk_color(float(days_in_stage), target_days)

        age_days = days_in_stage
        if age_days <= 7:
            bucket_totals["0_7_days"] += 1
        elif age_days <= 14:
            bucket_totals["8_14_days"] += 1
        elif age_days <= 30:
            bucket_totals["15_30_days"] += 1
        else:
            bucket_totals["31_plus_days"] += 1

        if risk_color == "green":
            total_green += 1
        elif risk_color == "yellow":
            total_yellow += 1
        else:
            total_red += 1

        if stage_name in stage_rollup:
            stage_rollup[stage_name][risk_color] += 1
            stage_rollup[stage_name]["total_wip"] += 1
            stage_rollup[stage_name]["total_age_days"] += age_days

        if oldest_open_job is None or age_days > oldest_open_job["age_days"]:
            oldest_open_job = {
                "fab_id": fab_id,
                "job_number": job_number,
                "current_stage": stage_name if stage_name != "Other" else current_stage,
                "age_days": age_days,
                "due_date": due_date.isoformat() if due_date else None,
                "stage_anchor": stage_anchor.isoformat() if stage_anchor else None,
            }

        if stage_name == "Revisions":
            assigned_user_id = revision_assigned_to or drafter_id
        elif stage_name in {"Drafting", "Pre-Draft Review", "Final Programming", "CNC", "SlabSmith"}:
            assigned_user_id = drafter_id
        elif stage_name == "SCT":
            assigned_user_id = sales_person_id
        else:
            assigned_user_id = drafter_id or sales_person_id

        priority_flag = str(job_priority or "").strip() or ("High" if risk_color == "red" else "Medium")
        status_label = "On Track" if risk_color == "green" else "At Risk" if risk_color == "yellow" else "Over SLA"

        fab_status_rows.append(
            {
                "fab_type": fab_type,
                "fab_id": fab_id,
                "job_number": job_number,
                "fab_info": (f"{job_name or ''} | {round(_to_float(total_sqft), 2)} sqft | {int(_to_float(no_of_pieces))} pcs").strip(" |"),
                "current_stage": stage_name if stage_name != "Other" else current_stage,
                "days_since_template": days_since_template,
                "days_in_stage": days_in_stage,
                "revision_type": revision_type,
                "assigned_user": _first_name(user_names, assigned_user_id),
                "status": status_label,
                "priority_flag": priority_flag,
                "risk_color": risk_color,
                "stage_target_days": target_days,
            }
        )

        if risk_color == "red":
            breach_details.append(
                {
                    "fab_id": fab_id,
                    "job_number": job_number,
                    "current_stage": stage_name if stage_name != "Other" else current_stage,
                    "age_days": days_in_stage,
                    "sla_days": target_days,
                    "days_over_sla": round(days_in_stage - target_days, 2),
                    "stage_anchor": stage_anchor.isoformat() if stage_anchor else None,
                    "due_date": due_date.isoformat() if due_date else None,
                }
            )

    breach_details.sort(key=lambda row: row["days_over_sla"], reverse=True)
    total_breach_count = len(breach_details)
    breach_details = breach_details[:breach_limit]

    aging_backlog = [
        {"bucket": "0-7 days", "count": bucket_totals["0_7_days"]},
        {"bucket": "8-14 days", "count": bucket_totals["8_14_days"]},
        {"bucket": "15-30 days", "count": bucket_totals["15_30_days"]},
        {"bucket": "31+ days", "count": bucket_totals["31_plus_days"]},
    ]

    stage_bottleneck_heat_map = []
    for stage_name in stage_display_names:
        row = stage_rollup[stage_name]
        total_wip = int(row["total_wip"])
        avg_days = round((row["total_age_days"] / total_wip), 2) if total_wip else 0.0
        target_days = _target_days_for(stage_name, None)
        stage_bottleneck_heat_map.append(
            {
                "stage": stage_name,
                "target_days": target_days,
                "green": int(row["green"]),
                "yellow": int(row["yellow"]),
                "red": int(row["red"]),
                "total_wip": total_wip,
                "avg_days": avg_days,
                "sla_breach_percent": round((row["red"] / total_wip) * 100, 2) if total_wip else 0.0,
            }
        )

    on_time_percent = round((on_time_count / on_time_eligible) * 100, 2) if on_time_eligible else 0.0
    total_active_fab_ids = len(backlog_rows)

    widgets = {
        "total_active_fab_ids": total_active_fab_ids,
        "on_track_green": total_green,
        "at_risk_yellow": total_yellow,
        "overdue_red": total_red,
        "avg_cycle_time_days": cycle_stats["avg_days"],
        "oldest_open_job": oldest_open_job,
    }

    fab_status_rows.sort(
        key=lambda row: (
            2 if row["risk_color"] == "red" else 1 if row["risk_color"] == "yellow" else 0,
            row["days_in_stage"] or 0,
        ),
        reverse=True,
    )

    return success_response(
        {
            "title": "Service Level Report",
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "date_basis": date_basis,
                "sla_days": sla_days,
            },
            "widgets": widgets,
            "summary": {
                "total_completed": total_completed,
                "on_time_eligible": on_time_eligible,
                "on_time_count": on_time_count,
                "on_time_percent": on_time_percent,
                "open_backlog_count": sum(bucket_totals.values()),
                "sla_breach_count": total_breach_count,
                "green_count": total_green,
                "yellow_count": total_yellow,
                "red_count": total_red,
                "cycle_time_avg_days": cycle_stats["avg_days"],
                "cycle_time_min_days": cycle_stats["min_days"],
                "cycle_time_max_days": cycle_stats["max_days"],
            },
            "stage_bottleneck_heat_map": stage_bottleneck_heat_map,
            "sla_rules": {
                "green": "Within 75% of stage SLA threshold",
                "yellow": "75% to 100% of stage SLA threshold",
                "red": "Exceeds stage SLA threshold",
                "stage_target_days": {
                    "Pre-Draft Review": 2,
                    "Drafting": 3,
                    "Revisions - CAD": 1,
                    "Revisions - Template": 1,
                    "Revisions - Sales": 1,
                    "Revisions - Client": 2,
                    "SCT": 3,
                    "SlabSmith": 2,
                    "Final Programming": 2,
                    "CNC": 1,
                },
            },
            "fab_status_rows": fab_status_rows,
            "cycle_time_stats": [cycle_stats],
            "aging_backlog": aging_backlog,
            "breach_details": breach_details,
            "completed_rows": cycle_rows,
        },
        "Owner service level report generated",
    )


@router.get("/reports/owner/installer-rates", response_model=SuccessResponse[list[dict]])
async def get_installer_rates(
    installer_id: Optional[int] = Query(None, gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(
        InstallerRateHistory.id,
        InstallerRateHistory.installer_id,
        InstallerRateHistory.hourly_rate,
        InstallerRateHistory.effective_from,
        InstallerRateHistory.effective_to,
        InstallerRateHistory.is_active,
        User.first_name,
        User.last_name,
    ).join(User, User.id == InstallerRateHistory.installer_id, isouter=True)

    if installer_id is not None:
        query = query.where(InstallerRateHistory.installer_id == installer_id)

    query = query.order_by(InstallerRateHistory.installer_id, InstallerRateHistory.effective_from.desc())
    rows = (await db.execute(query)).all()

    data = [
        {
            "id": row[0],
            "installer_id": row[1],
            "installer_name": (f"{(row[6] or '').strip()} {(row[7] or '').strip()}".strip() or f"User {row[1]}"),
            "hourly_rate": round(_to_float(row[2]), 2),
            "effective_from": row[3].isoformat() if row[3] else None,
            "effective_to": row[4].isoformat() if row[4] else None,
            "is_active": bool(row[5]),
        }
        for row in rows
    ]

    return success_response(data, "Installer rates retrieved")


@router.post("/reports/owner/installer-rates", response_model=SuccessResponse[dict])
async def create_installer_rate(
    payload: InstallerRateUpsert,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    installer_exists = (
        await db.execute(select(User.id).where(User.id == payload.installer_id))
    ).scalar_one_or_none()
    if not installer_exists:
        return success_response(None, "Installer not found", status_code=404)

    if payload.effective_to and payload.effective_to < payload.effective_from:
        return success_response(None, "effective_to cannot be before effective_from", status_code=400)

    # Close previously active open-ended ranges to avoid overlapping active rates.
    open_rates = (
        await db.execute(
            select(InstallerRateHistory)
            .where(
                InstallerRateHistory.installer_id == payload.installer_id,
                InstallerRateHistory.is_active.is_(True),
                InstallerRateHistory.effective_to.is_(None),
                InstallerRateHistory.effective_from <= payload.effective_from,
            )
            .order_by(InstallerRateHistory.effective_from.desc())
        )
    ).scalars().all()

    for rate in open_rates:
        rate.effective_to = payload.effective_from
        rate.updated_at = datetime.now()
        rate.updated_by = current_user.id

    new_rate = InstallerRateHistory(
        installer_id=payload.installer_id,
        hourly_rate=payload.hourly_rate,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        is_active=payload.is_active,
        created_by=current_user.id,
    )
    db.add(new_rate)
    await db.commit()
    await db.refresh(new_rate)

    return success_response(
        {
            "id": new_rate.id,
            "installer_id": new_rate.installer_id,
            "hourly_rate": new_rate.hourly_rate,
            "effective_from": new_rate.effective_from.isoformat(),
            "effective_to": new_rate.effective_to.isoformat() if new_rate.effective_to else None,
            "is_active": new_rate.is_active,
        },
        "Installer rate created",
    )


@router.get("/reports/owner/management-packet", response_model=SuccessResponse[dict])
async def get_owner_management_packet(
    start_date: Optional[date] = Query(None, description="Inclusive start date filter"),
    end_date: Optional[date] = Query(None, description="Inclusive end date filter"),
    weeks: int = Query(12, ge=4, le=52, description="How many trailing weeks to include"),
    top_n: int = Query(10, ge=1, le=50, description="Top N for hotspot/installer blocks"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    overview = _unwrap_success_data(
        await get_owner_overview_report(start_date=start_date, end_date=end_date, db=db, current_user=current_user)
    )
    redo = _unwrap_success_data(
        await get_owner_redo_analysis_report(
            start_date=start_date,
            end_date=end_date,
            top_n=top_n,
            db=db,
            current_user=current_user,
        )
    )
    shop_status = _unwrap_success_data(
        await get_owner_shop_status_report(start_date=start_date, end_date=end_date, db=db, current_user=current_user)
    )
    install_perf = _unwrap_success_data(
        await get_owner_install_performance_report(
            start_date=start_date,
            end_date=end_date,
            top_n=top_n,
            db=db,
            current_user=current_user,
        )
    )
    weekly = _unwrap_success_data(
        await get_owner_weekly_trends_report(weeks=weeks, db=db, current_user=current_user)
    )

    return success_response(
        {
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "weeks": weeks,
            },
            "overview": overview,
            "redo_analysis": redo,
            "shop_status": shop_status,
            "install_performance": install_perf,
            "weekly_trends": weekly,
        },
        "Owner management packet generated",
    )


@router.get("/reports/owner/export/{report_key}")
async def export_owner_report(
    report_key: str,
    export_format: str = Query("csv", pattern="^(csv|xlsx|json)$"),
    layout: str = Query("default", pattern="^(default|client)$"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    date_basis: str = Query("completed", pattern="^(created|scheduled|completed)$"),
    sla_days: int = Query(14, ge=1, le=365),
    weeks: int = Query(12, ge=4, le=52),
    top_n: int = Query(10, ge=1, le=50),
    year: Optional[int] = Query(None, ge=2000, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    key = report_key.strip().lower()

    if key == "overview":
        data = _unwrap_success_data(
            await get_owner_overview_report(start_date=start_date, end_date=end_date, db=db, current_user=current_user)
        )
    elif key == "redo-analysis":
        data = _unwrap_success_data(
            await get_owner_redo_analysis_report(start_date=start_date, end_date=end_date, top_n=top_n, db=db, current_user=current_user)
        )
    elif key == "shop-status":
        data = _unwrap_success_data(
            await get_owner_shop_status_report(start_date=start_date, end_date=end_date, db=db, current_user=current_user)
        )
    elif key == "install-performance":
        data = _unwrap_success_data(
            await get_owner_install_performance_report(start_date=start_date, end_date=end_date, top_n=top_n, db=db, current_user=current_user)
        )
    elif key == "installation-template":
        data = _unwrap_success_data(
            await get_owner_installation_template_report(start_date=start_date, end_date=end_date, db=db, current_user=current_user)
        )
    elif key == "monthly-install-completion":
        if year is None or month is None:
            return success_response(None, "year and month are required for monthly-install-completion", status_code=400)
        data = _unwrap_success_data(
            await get_owner_monthly_install_completion_report(year=year, month=month, db=db, current_user=current_user)
        )
    elif key == "daily-install-completion":
        data = _unwrap_success_data(
            await get_owner_daily_install_completion_report(start_date=start_date, end_date=end_date, db=db, current_user=current_user)
        )
    elif key == "monthly-cut-completion":
        if year is None or month is None:
            return success_response(None, "year and month are required for monthly-cut-completion", status_code=400)
        data = _unwrap_success_data(
            await get_owner_monthly_cut_completion_report(year=year, month=month, db=db, current_user=current_user)
        )
    elif key == "turnaround-times":
        if year is None or month is None:
            return success_response(None, "year and month are required for turnaround-times", status_code=400)
        data = _unwrap_success_data(
            await get_owner_turnaround_times_report(year=year, month=month, db=db, current_user=current_user)
        )
    elif key == "service-level":
        data = _unwrap_success_data(
            await get_owner_service_level_report(
                start_date=start_date,
                end_date=end_date,
                date_basis=date_basis,
                sla_days=sla_days,
                db=db,
                current_user=current_user,
            )
        )
    elif key == "weekly-trends":
        data = _unwrap_success_data(
            await get_owner_weekly_trends_report(weeks=weeks, db=db, current_user=current_user)
        )
    elif key == "management-packet":
        data = _unwrap_success_data(
            await get_owner_management_packet(
                start_date=start_date,
                end_date=end_date,
                weeks=weeks,
                top_n=top_n,
                db=db,
                current_user=current_user,
            )
        )
    else:
        return success_response(None, f"Unsupported report_key '{report_key}'", status_code=400)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{key}_{stamp}.{export_format}"

    if export_format == "json":
        content = json.dumps(data, indent=2).encode("utf-8")
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    if export_format == "csv":
        content = _csv_bytes(key, data, layout=layout)
        return StreamingResponse(
            io.BytesIO(content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    content = _xlsx_bytes(key, data, layout=layout)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
