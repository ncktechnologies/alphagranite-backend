from __future__ import annotations
# pyright: reportGeneralTypeIssues=false, reportMissingImports=false

import csv
import io
import json
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import get_db
from src.app.database.account import Account
from src.app.database.business_job import BusinessJob
from src.app.database.fab import Fab
from src.app.database.installer_rate_history import InstallerRateHistory
from src.app.database.installer_job_timer_session import InstallerJobTimerSession
from src.app.database.user import User
from src.app.interface.generated_schemas import InstallCompletion, Revision
from src.app.interface.response_wrappers import SuccessResponse, success_response
from src.app.middleware.jwt_auth import get_current_user

router = APIRouter()


class InstallerRateUpsert(BaseModel):
    installer_id: int = Field(..., gt=0)
    hourly_rate: float = Field(..., gt=0)
    effective_from: datetime
    effective_to: Optional[datetime] = None
    is_active: bool = True


def _range_bounds(start_date: Optional[date], end_date: Optional[date]) -> tuple[Optional[datetime], Optional[datetime]]:
    start_dt = datetime.combine(start_date, time.min) if start_date else None
    end_dt = datetime.combine(end_date, time.max) if end_date else None
    return start_dt, end_dt


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


def _report_sections(report_key: str, data: dict) -> list[tuple[str, list[dict]]]:
    if report_key == "overview":
        return [
            ("kpis", [_rows_from_mapping(data.get("kpis", {}))[i] for i in range(len(_rows_from_mapping(data.get("kpis", {}))))]),
            ("stage_breakdown", data.get("stage_breakdown", [])),
        ]

    if report_key == "redo-analysis":
        return [
            ("summary", [_rows_from_mapping(data.get("summary", {}))[i] for i in range(len(_rows_from_mapping(data.get("summary", {}))))]),
            ("redo_by_stage", data.get("redo_by_stage", [])),
            ("top_accounts_with_redo", data.get("top_accounts_with_redo", [])),
            ("top_jobs_with_redo", data.get("top_jobs_with_redo", [])),
        ]

    if report_key == "shop-status":
        return [("stage_status", data.get("stage_status", []))]

    if report_key == "install-performance":
        return [
            ("summary", [_rows_from_mapping(data.get("summary", {}))[i] for i in range(len(_rows_from_mapping(data.get("summary", {}))))]),
            ("installer_breakdown", data.get("installer_breakdown", [])),
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


def _csv_bytes(report_key: str, data: dict) -> bytes:
    sections = _report_sections(report_key, data)
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


def _xlsx_bytes(report_key: str, data: dict) -> bytes:
    from openpyxl import Workbook  # type: ignore[reportMissingImports]

    sections = _report_sections(report_key, data)
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

    fab_week_rows = (
        await db.execute(
            select(
                func.date_trunc("week", Fab.created_at).label("week_start"),
                func.count(Fab.id).label("fabs_created"),
                func.sum(Fab.revenue).label("revenue"),
                func.sum(Fab.gp).label("gp"),
            )
            .where(Fab.created_at >= cutoff)
            .group_by(func.date_trunc("week", Fab.created_at))
            .order_by(func.date_trunc("week", Fab.created_at))
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
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    weeks: int = Query(12, ge=4, le=52),
    top_n: int = Query(10, ge=1, le=50),
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
        content = _csv_bytes(key, data)
        return StreamingResponse(
            io.BytesIO(content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    content = _xlsx_bytes(key, data)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
