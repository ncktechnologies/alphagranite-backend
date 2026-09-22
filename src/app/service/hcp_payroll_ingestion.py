import asyncio
import io
import logging
import os
import json
from datetime import datetime
from typing import Any, Optional

from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.hcp_payroll import (
    HcpPayrollIngestionRun,
    HcpPayrollReportRow,
    HcpPayrollReportSnapshot,
    HcpPayrollSourceConfig,
    HcpStaffRosterRow,
    HcpStaffRosterSnapshot,
)
from src.app.hcp_payroll_parser import (
    ParsedHcpPayrollRow,
    parse_hcp_payroll_report,
    parse_hcp_staff_roster,
)
from src.app.utils.config import SessionLocal
from src.app.utils.helpers import utc_now

logger = logging.getLogger("hcp_payroll_ingestion")

DEFAULT_BASE_URL = "https://secure.saashr.com"
STAFF_ROSTER_REPORT_KIND = "staff_roster"

_scheduler_task: Optional[asyncio.Task] = None
_last_trigger_keys: dict[int, str] = {}


def get_default_base_url() -> str:
    return (os.getenv("HCP_BASE_URL") or DEFAULT_BASE_URL).strip().rstrip("/") or DEFAULT_BASE_URL


def _normalize_base_url(base_url: str) -> str:
    return (base_url or "").strip().rstrip("/") or get_default_base_url()


def _join_url(base_url: str, path: str) -> str:
    return f"{_normalize_base_url(base_url)}{path}"


async def _get_active_configs(db: AsyncSession) -> list[HcpPayrollSourceConfig]:
    result = await db.execute(select(HcpPayrollSourceConfig).where(HcpPayrollSourceConfig.is_active.is_(True)))
    return list(result.scalars().all())


async def _fetch_access_token(config: HcpPayrollSourceConfig) -> tuple[str, dict[str, Any]]:
    token_url = _join_url(
        config.base_url,
        f"/ta/rest/v2/companies/{config.company_id}/oauth2/token",
    )
    form_data = {
        "grant_type": config.grant_type or "client_credentials",
        "client_id": config.client_id or "",
        "client_secret": config.client_secret or "",
    }

    def _request_token() -> dict[str, Any]:
        request = Request(
            token_url,
            data=urlencode(form_data).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))

    try:
        token_data = await asyncio.to_thread(_request_token)
    except (HTTPError, URLError, ValueError) as exc:
        raise RuntimeError(f"Failed to fetch HCP access token: {exc}") from exc

    access_token = token_data.get("access_token")
    if not access_token:
        raise ValueError("HCP token response did not include an access_token")

    return access_token, token_data


async def _fetch_saved_report(config: HcpPayrollSourceConfig, access_token: str) -> tuple[str, int, str]:
    report_url = _join_url(config.base_url, f"/ta/rest/v1/report/saved/{config.report_settings_id}")

    def _request_report() -> tuple[str, int, str]:
        request = Request(
            report_url,
            headers={"Authorization": f"Bearer {access_token}"},
            method="GET",
        )
        with urlopen(request, timeout=120) as response:
            content_type = response.headers.get("content-type", "")
            return response.read().decode("utf-8"), getattr(response, "status", 200), content_type

    try:
        return await asyncio.to_thread(_request_report)
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"Failed to fetch HCP saved report: {exc}") from exc


async def ingest_hcp_payroll_report(
    db: AsyncSession,
    source_config_id: Optional[int] = None,
    triggered_by_user_id: Optional[int] = None,
) -> dict[str, Any]:
    if source_config_id is None:
        active_configs = await _get_active_configs(db)
        if not active_configs:
            return {"status": "skipped", "reason": "no_active_configs"}
        return {
            "status": "queued",
            "config_results": [
                await ingest_hcp_payroll_report(db, config.id, triggered_by_user_id) for config in active_configs
            ],
        }

    config = await db.get(HcpPayrollSourceConfig, source_config_id)
    if not config:
        raise ValueError(f"HCP payroll source config {source_config_id} not found")

    run = HcpPayrollIngestionRun(
        source_config_id=config.id,
        status="running",
        created_by=triggered_by_user_id,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    try:
        access_token, token_data = await _fetch_access_token(config)
        run.token_request_url = _join_url(config.base_url, f"/ta/rest/v2/companies/{config.company_id}/oauth2/token")
        run.token_response_json = token_data
        run.token_acquired_at = utc_now()
        run.token_expires_in = int(token_data.get("expires_in") or 0) if token_data.get("expires_in") is not None else None
        await db.commit()

        raw_report_text, report_http_status, report_content_type = await _fetch_saved_report(config, access_token)
        run.report_request_url = _join_url(config.base_url, f"/ta/rest/v1/report/saved/{config.report_settings_id}")
        run.report_http_status = report_http_status
        run.report_content_type = report_content_type

        if (config.report_kind or "").strip().lower() == STAFF_ROSTER_REPORT_KIND:
            result = await _store_staff_roster(db, config, run, raw_report_text)
        else:
            result = await _store_labor_cost_report(db, config, run, raw_report_text)

        run.row_count = result["row_count"]
        run.status = "completed"
        run.finished_at = utc_now()
        await db.commit()
        await db.refresh(run)

        return {"status": "completed", "run_id": run.id, **result}
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)
        run.finished_at = utc_now()
        await db.commit()
        logger.exception("Failed to ingest HCP payroll report for config %s", config.id)
        raise


async def _store_labor_cost_report(
    db: AsyncSession,
    config: HcpPayrollSourceConfig,
    run: HcpPayrollIngestionRun,
    raw_report_text: str,
) -> dict[str, Any]:
    parsed_rows = parse_hcp_payroll_report(raw_report_text)
    snapshot = HcpPayrollReportSnapshot(
        source_config_id=config.id,
        ingestion_run_id=run.id,
        report_settings_id=config.report_settings_id,
        payload_format="text",
        raw_payload_text=raw_report_text,
        row_count=len(parsed_rows),
    )
    db.add(snapshot)
    await db.flush()

    for parsed_row in parsed_rows:
        db.add(
            HcpPayrollReportRow(
                snapshot_id=snapshot.id,
                source_config_id=config.id,
                ingestion_run_id=run.id,
                row_kind=parsed_row.row_kind,
                row_index=parsed_row.row_index,
                cost_center_name=parsed_row.cost_center_name,
                employee_first_name=parsed_row.employee_first_name,
                employee_last_name=parsed_row.employee_last_name,
                hourly_pay=parsed_row.hourly_pay,
                regular_hours=parsed_row.regular_hours,
                holiday_hours=parsed_row.holiday_hours,
                pto_hours=parsed_row.pto_hours,
                total_reg_pto_hol_wages=parsed_row.total_reg_pto_hol_wages,
                overtime_hours=parsed_row.overtime_hours,
                total_ot_wages=parsed_row.total_ot_wages,
                raw_line_text=parsed_row.raw_line_text,
            )
        )

    return {
        "report_kind": "labor_cost",
        "snapshot_id": snapshot.id,
        "row_count": len(parsed_rows),
    }


async def _store_staff_roster(
    db: AsyncSession,
    config: HcpPayrollSourceConfig,
    run: HcpPayrollIngestionRun,
    raw_report_text: str,
) -> dict[str, Any]:
    parsed_rows = parse_hcp_staff_roster(raw_report_text)
    active_rows = [row for row in parsed_rows if row.is_active]

    snapshot = HcpStaffRosterSnapshot(
        source_config_id=config.id,
        ingestion_run_id=run.id,
        report_settings_id=config.report_settings_id,
        payload_format="csv",
        raw_payload_text=raw_report_text,
        pulled_at=utc_now(),
        row_count=len(parsed_rows),
        active_employee_count=len(active_rows),
    )
    db.add(snapshot)
    await db.flush()

    for parsed_row in parsed_rows:
        db.add(
            HcpStaffRosterRow(
                snapshot_id=snapshot.id,
                source_config_id=config.id,
                ingestion_run_id=run.id,
                row_index=parsed_row.row_index,
                employee_id=parsed_row.employee_id,
                username=parsed_row.username,
                first_name=parsed_row.first_name,
                last_name=parsed_row.last_name,
                employee_status=parsed_row.employee_status,
                employee_type=parsed_row.employee_type,
                in_payroll=parsed_row.in_payroll,
                locked=parsed_row.locked,
                date_terminated=parsed_row.date_terminated,
                is_active=parsed_row.is_active,
                raw_line_text=parsed_row.raw_line_text,
            )
        )

    return {
        "report_kind": STAFF_ROSTER_REPORT_KIND,
        "snapshot_id": snapshot.id,
        "row_count": len(parsed_rows),
        "active_employee_count": len(active_rows),
    }


async def get_active_configs(db: AsyncSession) -> list[HcpPayrollSourceConfig]:
    return await _get_active_configs(db)


async def preview_hcp_payroll_report(db: AsyncSession, source_config_id: int, max_rows: int = 10) -> dict[str, Any]:
    """Fetch token + report and parse it without writing snapshots, for connectivity testing."""
    config = await db.get(HcpPayrollSourceConfig, source_config_id)
    if not config:
        raise ValueError(f"HCP payroll source config {source_config_id} not found")

    access_token, token_data = await _fetch_access_token(config)
    raw_report_text, report_http_status, report_content_type = await _fetch_saved_report(config, access_token)

    report_kind = (config.report_kind or "labor_cost").strip().lower()
    if report_kind == STAFF_ROSTER_REPORT_KIND:
        parsed = parse_hcp_staff_roster(raw_report_text)
        sample = [vars(row) for row in parsed[:max_rows]]
        active_employee_count = sum(1 for row in parsed if row.is_active)
    else:
        parsed = parse_hcp_payroll_report(raw_report_text)
        sample = [vars(row) for row in parsed[:max_rows]]
        active_employee_count = None

    return {
        "status": "ok",
        "persisted": False,
        "report_kind": report_kind,
        "base_url": _normalize_base_url(config.base_url),
        "report_settings_id": config.report_settings_id,
        "token_type": token_data.get("token_type"),
        "token_expires_in": token_data.get("expires_in"),
        "report_http_status": report_http_status,
        "report_content_type": report_content_type,
        "row_count": len(parsed),
        "active_employee_count": active_employee_count,
        "raw_payload_preview": raw_report_text[:2000],
        "sample_rows": sample,
    }


def is_config_due(config: HcpPayrollSourceConfig, now: datetime) -> bool:
    if not config.is_active:
        return False
    if config.schedule_type == "daily":
        return now.hour == config.schedule_hour and now.minute == config.schedule_minute
    if config.schedule_type == "interval":
        return now.hour == config.schedule_hour and now.minute == config.schedule_minute
    return now.weekday() == config.schedule_weekday and now.hour == config.schedule_hour and now.minute == config.schedule_minute


async def _scheduler_loop() -> None:
    global _last_trigger_keys

    while True:
        now = utc_now()
        trigger_key = now.strftime("%Y-%m-%d %H:%M")

        async with SessionLocal() as db:
            configs = await _get_active_configs(db)
            for config in configs:
                if not is_config_due(config, now):
                    continue

                config_key = f"{config.id}:{trigger_key}"
                if _last_trigger_keys.get(config.id) == config_key:
                    continue

                try:
                    await ingest_hcp_payroll_report(db, config.id)
                except Exception:
                    logger.exception("Failed scheduled HCP payroll ingestion for config %s", config.id)
                _last_trigger_keys[config.id] = config_key

        await asyncio.sleep(60)


def start_hcp_payroll_scheduler() -> None:
    global _scheduler_task

    is_enabled = os.getenv("HCP_PAYROLL_SCHEDULER_ENABLED", "true").strip().lower() == "true"
    if not is_enabled:
        logger.info("HCP payroll scheduler is disabled")
        return

    if _scheduler_task and not _scheduler_task.done():
        return

    _scheduler_task = asyncio.create_task(_scheduler_loop())
    logger.info("HCP payroll scheduler started")


async def stop_hcp_payroll_scheduler() -> None:
    global _scheduler_task

    if _scheduler_task is None:
        return

    _scheduler_task.cancel()
    try:
        await _scheduler_task
    except asyncio.CancelledError:
        pass
    finally:
        _scheduler_task = None
        logger.info("HCP payroll scheduler stopped")