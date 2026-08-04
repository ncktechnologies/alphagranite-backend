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
)
from src.app.database.user import User
from src.app.middleware.jwt_auth import get_current_user
from src.app.service.hcp_payroll_ingestion import ingest_hcp_payroll_report
from src.app.utils.helpers import error_response, success_response

router = APIRouter(prefix="/hcp-payroll", tags=["HCP Payroll"])


class HcpPayrollSourceConfigCreate(BaseModel):
    name: str
    base_url: str = Field(default="https://secure.saashr.com")
    company_id: str = Field(default="83943830")
    grant_type: str = Field(default="client_credentials")
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    report_settings_id: str = Field(default="89798180")
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
    report_settings_id: Optional[str] = None
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
        "report_settings_id": config.report_settings_id,
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
        base_url=payload.base_url,
        company_id=payload.company_id,
        grant_type=payload.grant_type,
        client_id=payload.client_id,
        client_secret=payload.client_secret,
        report_settings_id=payload.report_settings_id,
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
    setting.updated_at = datetime.now()
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


@router.post("/settings/{setting_id}/ingest")
async def ingest_setting(
    setting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(current_user)
    result = await ingest_hcp_payroll_report(db, setting_id, triggered_by_user_id=current_user.id)
    return success_response(result, "HCP payroll ingestion completed successfully")


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