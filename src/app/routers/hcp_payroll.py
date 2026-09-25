from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import get_db
from src.app.database.hcp_payroll import (
    HcpPayrollIngestionRun,
    HcpPayrollReportRow,
    HcpPayrollReportSnapshot,
    HcpPayrollSourceConfig,
    HcpStaffRosterRow,
    HcpStaffRosterSnapshot,
)
from src.app.database.user import User
from src.app.middleware.jwt_auth import get_current_user
from src.app.service.hcp_payroll_ingestion import (
    get_default_base_url,
    ingest_hcp_payroll_report,
    preview_hcp_payroll_report,
)
from src.app.utils.helpers import error_response, success_response, utc_now

router = APIRouter(prefix="/hcp-payroll", tags=["HCP Payroll"])


class HcpPayrollSourceConfigCreate(BaseModel):
    name: str
    base_url: Optional[str] = None
    company_id: str = Field(default="83943830")
    grant_type: str = Field(default="client_credentials")
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    payroll_settings_id: str = Field(default="89798180")
    roster_settings_id: str = Field(default="93428419")
    schedule_type: str = Field(default="weekly")
    schedule_interval: int = Field(default=1, ge=1)
    schedule_weekday: int = Field(default=0, ge=0, le=6)
    schedule_hour: int = Field(default=1, ge=0, le=23)
    schedule_minute: int = Field(default=0, ge=0, le=59)
    is_active: bool = True


class HcpPayrollSourceConfigUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    company_id: Optional[str] = None
    grant_type: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    payroll_settings_id: Optional[str] = None
    roster_settings_id: Optional[str] = None
    schedule_type: Optional[str] = None
    schedule_interval: Optional[int] = Field(default=None, ge=1)
    schedule_weekday: Optional[int] = Field(default=None, ge=0, le=6)
    schedule_hour: Optional[int] = Field(default=None, ge=0, le=23)
    schedule_minute: Optional[int] = Field(default=None, ge=0, le=59)
    is_active: Optional[bool] = None


def _require_admin(current_user: User) -> None:
    if not getattr(current_user, "is_super_admin", False):
        raise error_response("Admin access required", 403)


def _serialize_config(config: HcpPayrollSourceConfig) -> dict:
    return {
        "id": config.id,
        "name": config.name,
        "base_url": config.base_url,
        "company_id": config.company_id,
        "grant_type": config.grant_type,
        "client_id": config.client_id,
        "client_secret": config.client_secret,
        "payroll_settings_id": config.payroll_settings_id,
        "roster_settings_id": config.roster_settings_id,
        "schedule_type": config.schedule_type,
        "schedule_interval": config.schedule_interval,
        "schedule_weekday": config.schedule_weekday,
        "schedule_hour": config.schedule_hour,
        "schedule_minute": config.schedule_minute,
        "is_active": config.is_active,
        "created_at": config.created_at.isoformat() if config.created_at else None,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
    }


def _serialize_run(run: HcpPayrollIngestionRun) -> dict:
    return {
        "id": run.id,
        "source_config_id": run.source_config_id,
        "status": run.status,
        "token_request_url": run.token_request_url,
        "token_response_json": run.token_response_json,
        "token_acquired_at": run.token_acquired_at.isoformat() if run.token_acquired_at else None,
        "token_expires_in": run.token_expires_in,
        "report_request_url": run.report_request_url,
        "report_http_status": run.report_http_status,
        "report_content_type": run.report_content_type,
        "error_message": run.error_message,
        "row_count": run.row_count,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }


@router.get("/settings")
async def list_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(current_user)
    result = await db.execute(select(HcpPayrollSourceConfig).order_by(HcpPayrollSourceConfig.id.asc()))
    return success_response([_serialize_config(item) for item in result.scalars().all()], "HCP payroll settings retrieved successfully")


@router.post("/settings")
async def create_setting(
    payload: HcpPayrollSourceConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(current_user)
    setting = HcpPayrollSourceConfig(
        name=payload.name,
        base_url=payload.base_url or get_default_base_url(),
        company_id=payload.company_id,
        grant_type=payload.grant_type,
        client_id=payload.client_id,
        client_secret=payload.client_secret,
        payroll_settings_id=payload.payroll_settings_id,
        roster_settings_id=payload.roster_settings_id,
        schedule_type=payload.schedule_type,
        schedule_interval=payload.schedule_interval,
        schedule_weekday=payload.schedule_weekday,
        schedule_hour=payload.schedule_hour,
        schedule_minute=payload.schedule_minute,
        is_active=payload.is_active,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(setting)
    await db.commit()
    await db.refresh(setting)
    return success_response(_serialize_config(setting), "HCP payroll setting created successfully")


@router.put("/settings/{setting_id}")
async def update_setting(
    setting_id: int,
    payload: HcpPayrollSourceConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(current_user)
    setting = await db.get(HcpPayrollSourceConfig, setting_id)
    if not setting:
        raise error_response("HCP payroll setting not found", 404)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(setting, field, value)
    setting.updated_by = current_user.id
    setting.updated_at = utc_now()
    await db.commit()
    await db.refresh(setting)
    return success_response(_serialize_config(setting), "HCP payroll setting updated successfully")


@router.get("/runs")
async def list_runs(
    setting_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(current_user)
    query = select(HcpPayrollIngestionRun).order_by(HcpPayrollIngestionRun.id.desc())
    if setting_id is not None:
        query = query.where(HcpPayrollIngestionRun.source_config_id == setting_id)
    result = await db.execute(query)
    return success_response([_serialize_run(item) for item in result.scalars().all()], "HCP payroll runs retrieved successfully")


async def _resolve_active_config_id(db: AsyncSession) -> int:
    result = await db.execute(
        select(HcpPayrollSourceConfig)
        .where(HcpPayrollSourceConfig.is_active.is_(True))
        .order_by(HcpPayrollSourceConfig.id.asc())
    )
    config = result.scalars().first()
    if not config:
        raise error_response("No active HCP payroll configuration found", 404)
    return config.id


@router.post("/ingest")
async def ingest_active(
    report_kind: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pull both saved reports for every active configuration."""
    _require_admin(current_user)
    result = await ingest_hcp_payroll_report(
        db, None, triggered_by_user_id=current_user.id, report_kind=report_kind
    )
    return success_response(result, "HCP payroll ingestion completed successfully")


@router.post("/test")
async def test_active(
    max_rows: int = 10,
    report_kind: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dry run against the active configuration; persists nothing."""
    _require_admin(current_user)
    config_id = await _resolve_active_config_id(db)
    try:
        result = await preview_hcp_payroll_report(db, config_id, max_rows=max_rows, report_kind=report_kind)
    except ValueError as exc:
        raise error_response(str(exc), 404)
    except RuntimeError as exc:
        raise error_response(str(exc), 502)
    return success_response(result, "HCP payroll connection test completed successfully")


@router.post("/settings/{config_id}/ingest")
async def ingest_setting(
    config_id: int,
    report_kind: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pull every configured saved report (or one kind) using a single access token."""
    _require_admin(current_user)
    result = await ingest_hcp_payroll_report(
        db, config_id, triggered_by_user_id=current_user.id, report_kind=report_kind
    )
    return success_response(result, "HCP payroll ingestion completed successfully")


@router.post("/settings/{config_id}/test")
async def test_setting(
    config_id: int,
    max_rows: int = 10,
    report_kind: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dry run: authenticates and fetches the reports without persisting anything."""
    _require_admin(current_user)
    try:
        result = await preview_hcp_payroll_report(db, config_id, max_rows=max_rows, report_kind=report_kind)
    except ValueError as exc:
        raise error_response(str(exc), 404)
    except RuntimeError as exc:
        raise error_response(str(exc), 502)
    return success_response(result, "HCP payroll connection test completed successfully")


@router.get("/snapshots/{setting_id}")
async def list_snapshots(
    setting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(current_user)
    result = await db.execute(
        select(HcpPayrollReportSnapshot).where(HcpPayrollReportSnapshot.source_config_id == setting_id).order_by(HcpPayrollReportSnapshot.id.desc())
    )
    snapshots = [
        {
            "id": item.id,
            "source_config_id": item.source_config_id,
            "ingestion_run_id": item.ingestion_run_id,
            "report_settings_id": item.report_settings_id,
            "report_title": item.report_title,
            "payload_format": item.payload_format,
            "row_count": item.row_count,
            "period_start": item.period_start.isoformat() if item.period_start else None,
            "period_end": item.period_end.isoformat() if item.period_end else None,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in result.scalars().all()
    ]
    return success_response(snapshots, "HCP payroll snapshots retrieved successfully")


@router.get("/snapshots/{snapshot_id}/rows")
async def list_snapshot_rows(
    snapshot_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(current_user)
    result = await db.execute(
        select(HcpPayrollReportRow).where(HcpPayrollReportRow.snapshot_id == snapshot_id).order_by(HcpPayrollReportRow.row_index.asc(), HcpPayrollReportRow.id.asc())
    )
    rows = [
        {
            "id": item.id,
            "snapshot_id": item.snapshot_id,
            "row_kind": item.row_kind,
            "row_index": item.row_index,
            "cost_center_name": item.cost_center_name,
            "employee_id": item.employee_id,
            "employee_first_name": item.employee_first_name,
            "employee_last_name": item.employee_last_name,
            "hourly_pay": item.hourly_pay,
            "regular_hours": item.regular_hours,
            "holiday_hours": item.holiday_hours,
            "pto_hours": item.pto_hours,
            "total_reg_pto_hol_wages": item.total_reg_pto_hol_wages,
            "overtime_hours": item.overtime_hours,
            "total_ot_wages": item.total_ot_wages,
            "raw_line_text": item.raw_line_text,
        }
        for item in result.scalars().all()
    ]
    return success_response(rows, "HCP payroll rows retrieved successfully")


def _serialize_roster_snapshot(snapshot: HcpStaffRosterSnapshot) -> dict:
    return {
        "id": snapshot.id,
        "source_config_id": snapshot.source_config_id,
        "ingestion_run_id": snapshot.ingestion_run_id,
        "report_settings_id": snapshot.report_settings_id,
        "payload_format": snapshot.payload_format,
        "pulled_at": snapshot.pulled_at.isoformat() if snapshot.pulled_at else None,
        "row_count": snapshot.row_count,
        "active_employee_count": snapshot.active_employee_count,
        "period_start": snapshot.period_start.isoformat() if snapshot.period_start else None,
        "period_end": snapshot.period_end.isoformat() if snapshot.period_end else None,
        "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None,
    }


@router.get("/staff-roster/snapshots")
async def list_staff_roster_snapshots(
    setting_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(current_user)
    query = select(HcpStaffRosterSnapshot).order_by(HcpStaffRosterSnapshot.id.desc())
    if setting_id is not None:
        query = query.where(HcpStaffRosterSnapshot.source_config_id == setting_id)
    result = await db.execute(query)
    return success_response(
        [_serialize_roster_snapshot(item) for item in result.scalars().all()],
        "HCP staff roster snapshots retrieved successfully",
    )


@router.get("/staff-roster/latest")
async def get_latest_staff_roster(
    setting_id: Optional[int] = None,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(current_user)
    snapshot_query = select(HcpStaffRosterSnapshot).order_by(HcpStaffRosterSnapshot.pulled_at.desc(), HcpStaffRosterSnapshot.id.desc()).limit(1)
    if setting_id is not None:
        snapshot_query = snapshot_query.where(HcpStaffRosterSnapshot.source_config_id == setting_id)
    snapshot = (await db.execute(snapshot_query)).scalars().first()
    if not snapshot:
        raise error_response("No HCP staff roster snapshot found", 404)

    rows_query = select(HcpStaffRosterRow).where(HcpStaffRosterRow.snapshot_id == snapshot.id)
    if active_only:
        rows_query = rows_query.where(HcpStaffRosterRow.is_active.is_(True))
    rows_query = rows_query.order_by(HcpStaffRosterRow.row_index.asc())
    rows = (await db.execute(rows_query)).scalars().all()

    return success_response(
        {
            "snapshot": _serialize_roster_snapshot(snapshot),
            "employees": [_serialize_roster_row(item) for item in rows],
        },
        "HCP staff roster retrieved successfully",
    )


def _serialize_roster_row(row: HcpStaffRosterRow) -> dict:
    return {
        "id": row.id,
        "snapshot_id": row.snapshot_id,
        "row_index": row.row_index,
        "employee_id": row.employee_id,
        "username": row.username,
        "first_name": row.first_name,
        "last_name": row.last_name,
        "employee_status": row.employee_status,
        "employee_type": row.employee_type,
        "in_payroll": row.in_payroll,
        "locked": row.locked,
        "date_terminated": row.date_terminated,
        "is_active": row.is_active,
    }


@router.get("/staff-roster/snapshots/{snapshot_id}/rows")
async def list_staff_roster_rows(
    snapshot_id: int,
    active_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(current_user)
    query = select(HcpStaffRosterRow).where(HcpStaffRosterRow.snapshot_id == snapshot_id)
    if active_only:
        query = query.where(HcpStaffRosterRow.is_active.is_(True))
    query = query.order_by(HcpStaffRosterRow.row_index.asc())
    result = await db.execute(query)
    return success_response(
        [_serialize_roster_row(item) for item in result.scalars().all()],
        "HCP staff roster rows retrieved successfully",
    )