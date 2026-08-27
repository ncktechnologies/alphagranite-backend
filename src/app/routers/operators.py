import mimetypes
import os
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File as FileUpload, Form, status
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.database import get_db
from src.app.database.account import Account
from src.app.database.business_job import BusinessJob
from src.app.database.file import File
from src.app.database.fab import Fab
from src.app.database.operator_job_timer_event import OperatorJobTimerEvent
from src.app.database.operator_job_timer_session import OperatorJobTimerSession
from src.app.interface.generated_schemas import PlanningSection, ShopRevision
from src.app.database.shop_cut_plan import ShopCutPlan
from src.app.database.stone_color import StoneColor
from src.app.database.stone_thickness import StoneThickness
from src.app.database.stone_type import StoneType
from src.app.database.user import User
from src.app.database.work_station import WorkStation
from src.app.database.edge import Edge
from src.app.interface.business_schemas import (
    OperatorJobTimerActionRequest,
    OperatorJobTimerCommandRequest,
    OperatorWorkstationTaskUpdateRequest,
)
from src.app.interface.response_wrappers import SuccessResponse
from src.app.middleware.jwt_auth import get_current_user
from src.app.service.file import FileService
from src.app.utils.config import get_settings
from src.app.utils.helpers import success_response
from src.app.utils.timer_guards import assert_no_active_timer_session, assert_no_pending_shop_revision


router = APIRouter(
    prefix="/operators",
    tags=["Operators"],
)


PHOTO_EXTS = {"jpg", "jpeg", "png", "gif", "webp", "heic", "bmp", "tiff"}


def _is_browser_renderable_file(name: Optional[str], file_type: Optional[str] = None) -> bool:
    filename = name or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in PHOTO_EXTS or ext == "pdf":
        return True

    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type and (mime_type.startswith("image/") or mime_type == "application/pdf"):
        return True

    return file_type == "photo"


def _build_operator_file_view_url(
    *,
    base_url: str,
    operator_id: int,
    job_id: Optional[int],
    file_id: Optional[int],
    file_name: Optional[str],
    file_path: Optional[str],
    file_type: Optional[str] = None,
) -> Optional[str]:
    if file_id is None:
        return None

    normalized_base_url = (base_url or "").strip()
    if normalized_base_url.startswith("http://"):
        normalized_base_url = f"https://{normalized_base_url[len('http://') :]}"

    # Return the simple file viewer URL which doesn't require operator/job context
    # and doesn't require auth token for browser viewing
    return f"{normalized_base_url}/api/v1/files/{file_id}/view"


def _serialize_operator_file(file: File, base_url: str, operator_id: int) -> dict:
    return {
        "id": file.id,
        "name": file.name,
        "file_url": _build_operator_file_view_url(
            base_url=base_url,
            operator_id=operator_id,
            job_id=file.job_id,
            file_id=file.id,
            file_name=file.name,
            file_path=file.file_path,
            file_type=file.file_type,
        ),
        "file_type": file.file_type,
        "file_size": file.file_size,
        "file_design": file.file_design or "",
        "stage_name": file.stage_name or "",
        "job_id": file.job_id,
        "fab_id": file.fab_id,
        "task_id": file.task_id,
        "uploaded_by": file.uploaded_by,
        "created_at": file.created_at.isoformat() if file.created_at else None,
    }


def _serialize_operator_task_file(file: File, base_url: str, operator_id: int) -> dict:
    return {
        "id": file.id,
        "name": file.name,
        "file_url": _build_operator_file_view_url(
            base_url=base_url,
            operator_id=operator_id,
            job_id=file.job_id,
            file_id=file.id,
            file_name=file.name,
            file_path=file.file_path,
            file_type=file.file_type,
        ),
        "file_type": file.file_type,
        "file_design": file.file_design or "",
        "fab_id": file.fab_id,
        "created_at": file.created_at.isoformat() if file.created_at else None,
    }


async def _get_operator_task_files(
    *,
    db: AsyncSession,
    operator_id: int,
    task_id: int,
    base_url: str,
) -> list[dict]:
    file_result = await db.execute(
        select(File)
        .where(File.task_id == task_id, File.uploaded_by == operator_id)
        .order_by(File.created_at.desc(), File.id.desc())
    )
    files = file_result.scalars().all()
    return [_serialize_operator_task_file(file, base_url, operator_id) for file in files]


async def _get_fab_connected_files(
    *,
    db: AsyncSession,
    operator_id: int,
    fab_id: int,
    base_url: str,
) -> list[dict]:
    """Return all files directly or indirectly associated with a FAB."""
    fab_task_ids_subquery = select(ShopCutPlan.id).where(ShopCutPlan.fab_id == fab_id)

    file_result = await db.execute(
        select(File)
        .where(
            or_(
                File.fab_id == fab_id,
                File.task_id.in_(fab_task_ids_subquery),
            )
        )
        .order_by(File.created_at.desc(), File.id.desc())
    )
    files = file_result.scalars().all()
    return [_serialize_operator_task_file(file, base_url, operator_id) for file in files]


def _serialize_workstation(ws: WorkStation, operators_by_id: dict = None, sections_by_id: dict = None) -> dict:
    operators_by_id = operators_by_id or {}
    sections_by_id = sections_by_id or {}

    operators = [
        {
            "id": uid,
            "name": f"{operators_by_id[uid].first_name} {operators_by_id[uid].last_name}".strip()
            if uid in operators_by_id else None,
        }
        for uid in (ws.operator_ids or [])
    ]

    ps = sections_by_id.get(ws.planning_section_id) if ws.planning_section_id else None

    return {
        "id": ws.id,
        "name": ws.name,
        "status_id": ws.status_id,
        "planning_section_id": ws.planning_section_id,
        "planning_section_name": ps.plan_name if ps else None,
        "operators": operators,
        "created_at": ws.created_at.isoformat() if ws.created_at else None,
        "created_by": ws.created_by,
        "updated_at": ws.updated_at.isoformat() if ws.updated_at else None,
        "updated_by": ws.updated_by,
    }


def _compute_schedule_end_time_iso(
    scheduled_start: Optional[datetime],
    estimated_hours: Optional[float],
) -> Optional[str]:
    if not scheduled_start or estimated_hours is None:
        return None
    try:
        return (scheduled_start + timedelta(hours=float(estimated_hours))).isoformat()
    except (TypeError, ValueError):
        return None


def _build_calendar_window(view: str, reference_date: date) -> tuple[datetime, datetime]:
    start_of_day = datetime.combine(reference_date, datetime.min.time())

    if view == "day":
        return start_of_day, start_of_day + timedelta(days=1)

    if view == "week":
        week_start = start_of_day - timedelta(days=reference_date.weekday())
        return week_start, week_start + timedelta(days=7)

    if view == "month":
        month_start = start_of_day.replace(day=1)
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month = month_start.replace(month=month_start.month + 1)
        return month_start, next_month

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="view must be one of: day, week, month")


def _serialize_operator_task(row, timer_status_by_fab: Optional[dict[int, str]] = None) -> dict:
    plan = row[0]
    fab = row[1]
    timer_status = (timer_status_by_fab or {}).get(plan.fab_id, "not_started")

    return {
        "task_id": plan.id,
        "fab_id": plan.fab_id,
        "job_id": fab.job_id,
        "job_name": row[2],
        "job_number": row[3],
        "account_name": row[4],
        "fab_type": fab.fab_type,
        "current_stage": fab.current_stage,
        "workstation_id": plan.workstation_id,
        "workstation_name": row[5],
        "planning_section_id": plan.planning_section_id,
        "planning_section_name": row[6],
        "has_pending_shop_revision": bool(row[7]),
        "sequence": plan.sequence,
        "scheduled_start_date": plan.scheduled_start_date.isoformat() if plan.scheduled_start_date else None,
        "scheduled_end_date": _compute_schedule_end_time_iso(plan.scheduled_start_date, plan.estimated_hours),
        "actual_start_date": plan.actual_start_date.isoformat() if plan.actual_start_date else None,
        "actual_end_date": plan.actual_end_date.isoformat() if plan.actual_end_date else None,
        "estimated_hours": float(plan.estimated_hours) if plan.estimated_hours is not None else None,
        "work_percentage": plan.work_percentage,
        "notes": plan.notes,
        "is_completed": bool(plan.actual_end_date) or plan.work_percentage == 100,
        "timer_status": timer_status,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
    }


def _serialize_operator_workstation_task(
    row,
    *,
    operator: User,
    total_actual_hours: float,
    total_actual_seconds: int,
    run_time: Optional[str] = None,
) -> dict:
    plan = row[0]
    fab = row[1]
    job = row[2]
    account_name = row[3]
    workstation_name = row[4]
    plan_name = row[5]
    stone_type_name = row[6]
    stone_color_name = row[7]
    stone_thickness_value = row[8]
    edge_name = row[9]
    operator_name = f"{operator.first_name} {operator.last_name}".strip() or operator.username
    estimated_hours = float(plan.estimated_hours) if plan.estimated_hours is not None else None

    return {
        "id": plan.id,
        "fab_id": plan.fab_id,
        "fab_type": fab.fab_type,
        "account_name": account_name,
        "job_name": job.name,
        "job_number": job.job_number,
        "business_job": {
            "id": job.id,
            "name": job.name,
            "job_number": job.job_number,
            "account_id": job.account_id,
            "account_name": account_name,
            "description": job.description,
            "priority": job.priority,
            "start_date": job.start_date.isoformat() if job.start_date else None,
            "due_date": job.due_date.isoformat() if job.due_date else None,
            "project_value": str(job.project_value) if job.project_value is not None else None,
            "status_id": job.status_id,
        },
        "sequence": plan.sequence,
        "workstation_id": plan.workstation_id,
        "workstation_name": workstation_name,
        "planning_section_id": plan.planning_section_id,
        "plan_name": plan_name,
        "operator_id": operator.id,
        "operator_name": operator_name,
        "estimated_hours": estimated_hours,
        "total_actual_seconds": total_actual_seconds,
        "total_actual_hours": total_actual_hours,
        "scheduled_start_date": plan.scheduled_start_date.isoformat() if plan.scheduled_start_date else None,
        "est_workstation_comp_date": _compute_schedule_end_time_iso(plan.scheduled_start_date, plan.estimated_hours),
        "est_job_comp_date": fab.shop_est_completion_date.date().isoformat() if fab.shop_est_completion_date else None,
        "actual_start_date": plan.actual_start_date.isoformat() if plan.actual_start_date else None,
        "actual_end_date": plan.actual_end_date.isoformat() if plan.actual_end_date else None,
        "work_percentage": int(plan.work_percentage or 0),
        "notes": plan.notes,
        "area": fab.input_area,
        "stone_type": stone_type_name,
        "stone_color": stone_color_name,
        "stone_thickness": stone_thickness_value,
        "edge": edge_name,
        "no_of_pieces": fab.no_of_pieces,
        "total_sqft": fab.total_sqft,
        "run_time": run_time,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
    }


def _format_seconds_to_hms(total_seconds: int) -> str:
    seconds = max(0, int(total_seconds or 0))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _current_session_run_time(active_session: OperatorJobTimerSession, as_of: datetime) -> str:
    total_seconds = int(active_session.total_work_seconds or 0)
    if active_session.status == "running":
        run_start = _normalize_naive_dt(active_session.current_run_start_at)
        if run_start and as_of > run_start:
            total_seconds += int((as_of - run_start).total_seconds())
    return _format_seconds_to_hms(total_seconds)


def _task_overlaps_window(plan: ShopCutPlan, range_start: datetime, range_end: datetime) -> bool:
    if not plan.scheduled_start_date:
        return False

    task_start = plan.scheduled_start_date
    if plan.estimated_hours is None:
        task_end = task_start
    else:
        try:
            task_end = task_start + timedelta(hours=float(plan.estimated_hours))
        except (TypeError, ValueError):
            task_end = task_start

    return task_start < range_end and task_end >= range_start


def _task_is_active(plan: ShopCutPlan) -> bool:
    return not bool(plan.actual_end_date) and int(plan.work_percentage or 0) < 100


def _group_tasks_by_day(tasks: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for task in tasks:
        scheduled_start = task.get("scheduled_start_date")
        key = scheduled_start[:10] if scheduled_start else "unscheduled"
        grouped.setdefault(key, []).append(task)

    grouped_days = []
    for day in sorted(grouped.keys()):
        grouped_days.append(
            {
                "date": day,
                "total": len(grouped[day]),
                "tasks": grouped[day],
            }
        )
    return grouped_days


def _normalize_naive_dt(value: Optional[datetime]) -> Optional[datetime]:
    return value.replace(tzinfo=None) if value and value.tzinfo else value


def _serialize_operator_job_timer_session(session: OperatorJobTimerSession) -> dict:
    return {
        "id": session.id,
        "fab_id": session.fab_id,
        "job_id": session.job_id,
        "operator_id": session.operator_id,
        "workstation_id": session.workstation_id,
        "status": session.status,
        "session_start_at": session.session_start_at.isoformat() if session.session_start_at else None,
        "current_run_start_at": session.current_run_start_at.isoformat() if session.current_run_start_at else None,
        "current_pause_start_at": session.current_pause_start_at.isoformat() if session.current_pause_start_at else None,
        "stopped_at": session.stopped_at.isoformat() if session.stopped_at else None,
        "total_work_seconds": int(session.total_work_seconds or 0),
        "total_pause_seconds": int(session.total_pause_seconds or 0),
    }


def _serialize_operator_job_timer_event(event: OperatorJobTimerEvent) -> dict:
    return {
        "id": event.id,
        "session_id": event.session_id,
        "fab_id": event.fab_id,
        "action": event.action,
        "event_at": event.event_at.isoformat() if event.event_at else None,
        "note": event.note,
        "workstation_id": event.workstation_id,
    }


async def _recalculate_operator_job_work_totals(
    db: AsyncSession,
    *,
    fab_id: Optional[int] = None,
    job_id: int,
    operator_id: int,
    as_of: datetime,
    workstation_id: Optional[int] = None,
) -> tuple[float, int]:
    if fab_id is not None:
        timer_scope_filter = or_(
            OperatorJobTimerSession.fab_id == fab_id,
            (OperatorJobTimerSession.fab_id.is_(None)) & (OperatorJobTimerSession.job_id == job_id),
        )
    else:
        timer_scope_filter = OperatorJobTimerSession.job_id == job_id

    totals_query = select(func.coalesce(func.sum(OperatorJobTimerSession.total_work_seconds), 0)).where(
            timer_scope_filter,
            OperatorJobTimerSession.operator_id == operator_id,
        )
    if workstation_id is not None:
        totals_query = totals_query.where(OperatorJobTimerSession.workstation_id == workstation_id)

    totals_result = await db.execute(totals_query)
    stored_seconds = int(totals_result.scalar() or 0)

    running_query = select(OperatorJobTimerSession).where(
        timer_scope_filter,
        OperatorJobTimerSession.operator_id == operator_id,
        OperatorJobTimerSession.status == "running",
        OperatorJobTimerSession.current_run_start_at.is_not(None),
    )
    if workstation_id is not None:
        running_query = running_query.where(OperatorJobTimerSession.workstation_id == workstation_id)

    running_result = await db.execute(running_query)
    running_sessions = running_result.scalars().all()

    in_progress_seconds = 0
    for session in running_sessions:
        run_start = _normalize_naive_dt(session.current_run_start_at)
        if run_start and as_of > run_start:
            in_progress_seconds += int((as_of - run_start).total_seconds())

    total_actual_seconds = max(0, stored_seconds + in_progress_seconds)
    total_actual_hours = total_actual_seconds / 3600.0
    return total_actual_hours, total_actual_seconds


async def _get_active_operator_job_session(
    db: AsyncSession,
    *,
    operator_id: int,
    fab_id: Optional[int] = None,
    job_id: Optional[int] = None,
    workstation_id: Optional[int] = None,
) -> Optional[OperatorJobTimerSession]:
    query = select(OperatorJobTimerSession).where(
        OperatorJobTimerSession.operator_id == operator_id,
        OperatorJobTimerSession.status.in_(["running", "paused"]),
    )
    if fab_id is not None:
        if job_id is not None:
            query = query.where(
                or_(
                    OperatorJobTimerSession.fab_id == fab_id,
                    (OperatorJobTimerSession.fab_id.is_(None)) & (OperatorJobTimerSession.job_id == job_id),
                )
            )
        else:
            query = query.where(OperatorJobTimerSession.fab_id == fab_id)
    elif job_id is not None:
        query = query.where(OperatorJobTimerSession.job_id == job_id)
    if workstation_id is not None:
        query = query.where(OperatorJobTimerSession.workstation_id == workstation_id)

    query = query.order_by(OperatorJobTimerSession.created_at.desc()).limit(1)
    result = await db.execute(query)
    return result.scalars().first()


async def _get_timer_statuses_for_fabs(
    db: AsyncSession,
    *,
    operator_id: int,
    fab_ids: list[int],
) -> dict[int, str]:
    """Return the latest timer session status per fab_id for the given operator."""

    if not fab_ids:
        return {}

    result = await db.execute(
        select(OperatorJobTimerSession)
        .where(
            OperatorJobTimerSession.operator_id == operator_id,
            OperatorJobTimerSession.fab_id.in_(fab_ids),
        )
        .order_by(OperatorJobTimerSession.fab_id, OperatorJobTimerSession.created_at.desc())
    )

    statuses: dict[int, str] = {}
    for session in result.scalars().all():
        if session.fab_id not in statuses:
            statuses[session.fab_id] = session.status
    return statuses



@router.get("/{operator_id}/workstations", response_model=SuccessResponse[dict])
async def get_workstations_by_operator(
    operator_id: int,
    status_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all workstations assigned to a specific operator."""

    operator_result = await db.execute(select(User).where(User.id == operator_id))
    operator = operator_result.scalar_one_or_none()
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator not found",
        )

    query = select(WorkStation).where(WorkStation.operator_ids.contains([operator_id]))

    if status_id is not None:
        query = query.where(WorkStation.status_id == status_id)

    if search:
        query = query.where(WorkStation.name.ilike(f"%{search}%"))

    count_query = select(func.count(WorkStation.id)).where(WorkStation.operator_ids.contains([operator_id]))
    if status_id is not None:
        count_query = count_query.where(WorkStation.status_id == status_id)
    if search:
        count_query = count_query.where(WorkStation.name.ilike(f"%{search}%"))

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    query = query.offset(skip).limit(limit).order_by(WorkStation.name)
    result = await db.execute(query)
    workstations = result.scalars().all()

    all_operator_ids = list({uid for ws in workstations for uid in (ws.operator_ids or [])})
    operators_by_id: dict = {}
    if all_operator_ids:
        ops_result = await db.execute(select(User).where(User.id.in_(all_operator_ids)))
        for u in ops_result.scalars().all():
            operators_by_id[u.id] = u

    all_ps_ids = list({ws.planning_section_id for ws in workstations if ws.planning_section_id is not None})
    sections_by_id: dict = {}
    if all_ps_ids:
        ps_result = await db.execute(select(PlanningSection).where(PlanningSection.id.in_(all_ps_ids)))
        for ps in ps_result.scalars().all():
            sections_by_id[ps.id] = ps

    operator_name = f"{operator.first_name} {operator.last_name}".strip()

    return success_response(
        {
            "operator_id": operator_id,
            "operator_name": operator_name or operator.username,
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "per_page": limit,
            "data": [_serialize_workstation(ws, operators_by_id, sections_by_id) for ws in workstations],
        },
        "Operator workstations retrieved successfully",
    )


@router.get("/{operator_id}/workstations/{workstation_id}/tasks")
async def get_workstation_tasks_by_operator(
    operator_id: int,
    workstation_id: int,
    view: str = Query("day"),
    selected_date: Optional[date] = Query(None, alias="date"),
    active_only: bool = Query(False),
    group_by_day: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all tasks assigned to an operator under a selected workstation, filtered by calendar window."""

    operator = (await db.execute(select(User).where(User.id == operator_id))).scalar_one_or_none()
    if not operator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operator not found")

    if not getattr(current_user, "is_super_admin", False) and current_user.id != operator_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this operator's tasks")

    workstation = (await db.execute(select(WorkStation).where(WorkStation.id == workstation_id))).scalar_one_or_none()
    if not workstation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workstation not found")

    if operator_id not in (workstation.operator_ids or []):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workstation is not assigned to this operator")

    normalized_view = (view or "day").strip().lower()
    target_date = selected_date or date.today()
    range_start, range_end = _build_calendar_window(normalized_view, target_date)

    query = (
        select(
            ShopCutPlan,
            Fab,
            BusinessJob,
            Account.name.label("account_name"),
            WorkStation.name.label("workstation_name"),
            PlanningSection.plan_name.label("plan_name"),
            StoneType.name.label("stone_type_name"),
            StoneColor.name.label("stone_color_name"),
            StoneThickness.thickness.label("stone_thickness_value"),
            Edge.name.label("edge_name"),
        )
        .join(Fab, Fab.id == ShopCutPlan.fab_id)
        .join(BusinessJob, BusinessJob.id == Fab.job_id)
        .join(Account, Account.id == BusinessJob.account_id, isouter=True)
        .join(WorkStation, WorkStation.id == ShopCutPlan.workstation_id, isouter=True)
        .join(PlanningSection, PlanningSection.id == ShopCutPlan.planning_section_id, isouter=True)
        .join(StoneType, StoneType.id == Fab.stone_type_id, isouter=True)
        .join(StoneColor, StoneColor.id == Fab.stone_color_id, isouter=True)
        .join(StoneThickness, StoneThickness.id == Fab.stone_thickness_id, isouter=True)
        .join(Edge, Edge.id == Fab.edge_id, isouter=True)
        .where(
            ShopCutPlan.user_id == operator_id,
            ShopCutPlan.workstation_id == workstation_id,
            ShopCutPlan.scheduled_start_date.is_not(None),
            ShopCutPlan.scheduled_start_date < range_end,
        )
        .order_by(ShopCutPlan.scheduled_start_date.asc(), ShopCutPlan.sequence.asc(), ShopCutPlan.id.asc())
    )

    rows = (await db.execute(query)).all()
    filtered_rows = [row for row in rows if _task_overlaps_window(row[0], range_start, range_end)]
    if active_only:
        filtered_rows = [row for row in filtered_rows if _task_is_active(row[0])]

    total = len(filtered_rows)
    paginated_rows = filtered_rows[skip:skip + limit]
    page = (skip // limit) + 1 if limit > 0 else 1

    tasks = []
    totals_cache: dict[int, tuple[float, int]] = {}
    for row in paginated_rows:
        job_id = row[2].id
        if job_id not in totals_cache:
            totals_cache[job_id] = await _recalculate_operator_job_work_totals(
                db=db,
                job_id=job_id,
                operator_id=operator_id,
                workstation_id=workstation_id,
                as_of=datetime.now().replace(second=0, microsecond=0),
            )
        total_actual_hours, total_actual_seconds = totals_cache[job_id]
        tasks.append(
            _serialize_operator_workstation_task(
                row,
                operator=operator,
                total_actual_hours=total_actual_hours,
                total_actual_seconds=total_actual_seconds,
                run_time=None,
            )
        )

    operator_name = f"{operator.first_name} {operator.last_name}".strip() or operator.username

    return {
        "success": True,
        "message": "Tasks retrieved successfully",
        "operator_id": operator_id,
        "operator_name": operator_name,
        "view": normalized_view,
        "date": target_date.isoformat(),
        "data": {
            "total": total,
            "page": page,
            "per_page": limit,
            "tasks": tasks,
            **({"grouped_tasks": _group_tasks_by_day(tasks)} if group_by_day else {}),
        },
    }


@router.get("/{operator_id}/workstations/{workstation_id}/tasks/{task_id}", response_model=SuccessResponse[dict])
async def get_workstation_task_by_id(
    operator_id: int,
    workstation_id: int,
    task_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a specific task assigned to an operator under a selected workstation."""

    operator = (await db.execute(select(User).where(User.id == operator_id))).scalar_one_or_none()
    if not operator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operator not found")

    if not getattr(current_user, "is_super_admin", False) and current_user.id != operator_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this operator's tasks")

    workstation = (await db.execute(select(WorkStation).where(WorkStation.id == workstation_id))).scalar_one_or_none()
    if not workstation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workstation not found")

    if operator_id not in (workstation.operator_ids or []):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workstation is not assigned to this operator")

    task_query = (
        select(
            ShopCutPlan,
            Fab,
            BusinessJob,
            Account.name.label("account_name"),
            WorkStation.name.label("workstation_name"),
            PlanningSection.plan_name.label("plan_name"),
            StoneType.name.label("stone_type_name"),
            StoneColor.name.label("stone_color_name"),
            StoneThickness.thickness.label("stone_thickness_value"),
            Edge.name.label("edge_name"),
        )
        .join(Fab, Fab.id == ShopCutPlan.fab_id)
        .join(BusinessJob, BusinessJob.id == Fab.job_id)
        .join(Account, Account.id == BusinessJob.account_id, isouter=True)
        .join(WorkStation, WorkStation.id == ShopCutPlan.workstation_id, isouter=True)
        .join(PlanningSection, PlanningSection.id == ShopCutPlan.planning_section_id, isouter=True)
        .join(StoneType, StoneType.id == Fab.stone_type_id, isouter=True)
        .join(StoneColor, StoneColor.id == Fab.stone_color_id, isouter=True)
        .join(StoneThickness, StoneThickness.id == Fab.stone_thickness_id, isouter=True)
        .join(Edge, Edge.id == Fab.edge_id, isouter=True)
        .where(
            ShopCutPlan.id == task_id,
            ShopCutPlan.workstation_id == workstation_id,
        )
        .limit(1)
    )

    task_row = (await db.execute(task_query)).first()
    if not task_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    job_id = task_row[2].id
    as_of = datetime.now().replace(second=0, microsecond=0)
    total_actual_hours, total_actual_seconds = await _recalculate_operator_job_work_totals(
        db=db,
        job_id=job_id,
        operator_id=operator_id,
        workstation_id=workstation_id,
        as_of=as_of,
    )

    active_session = await _get_active_operator_job_session(
        db,
        operator_id=operator_id,
        job_id=job_id,
        workstation_id=workstation_id,
    )

    task = _serialize_operator_workstation_task(
        task_row,
        operator=operator,
        total_actual_hours=total_actual_hours,
        total_actual_seconds=total_actual_seconds,
        run_time=_current_session_run_time(active_session, as_of) if active_session else None,
    )

    task["files"] = await _get_fab_connected_files(
        db=db,
        operator_id=operator_id,
        fab_id=task_row[1].id,
        base_url=FileService.get_base_url(request),
    )

    return success_response(task, "Task retrieved successfully")


@router.patch("/{operator_id}/workstations/{workstation_id}/tasks/{task_id}", response_model=SuccessResponse[dict])
async def update_workstation_task_by_id(
    operator_id: int,
    workstation_id: int,
    task_id: int,
    payload: OperatorWorkstationTaskUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a specific task assigned to an operator under a selected workstation."""

    if all(
        value is None
        for value in (
            payload.work_percentage,
            payload.actual_start_date,
            payload.actual_end_date,
            payload.notes,
        )
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one field is required")

    operator = (await db.execute(select(User).where(User.id == operator_id))).scalar_one_or_none()
    if not operator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operator not found")

    if not getattr(current_user, "is_super_admin", False) and current_user.id != operator_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this operator's tasks")

    workstation = (await db.execute(select(WorkStation).where(WorkStation.id == workstation_id))).scalar_one_or_none()
    if not workstation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workstation not found")

    if operator_id not in (workstation.operator_ids or []):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workstation is not assigned to this operator")

    task_query = (
        select(
            ShopCutPlan,
            Fab,
            BusinessJob,
            Account.name.label("account_name"),
            WorkStation.name.label("workstation_name"),
            PlanningSection.plan_name.label("plan_name"),
            StoneType.name.label("stone_type_name"),
            StoneColor.name.label("stone_color_name"),
            StoneThickness.thickness.label("stone_thickness_value"),
            Edge.name.label("edge_name"),
        )
        .join(Fab, Fab.id == ShopCutPlan.fab_id)
        .join(BusinessJob, BusinessJob.id == Fab.job_id)
        .join(Account, Account.id == BusinessJob.account_id, isouter=True)
        .join(WorkStation, WorkStation.id == ShopCutPlan.workstation_id, isouter=True)
        .join(PlanningSection, PlanningSection.id == ShopCutPlan.planning_section_id, isouter=True)
        .join(StoneType, StoneType.id == Fab.stone_type_id, isouter=True)
        .join(StoneColor, StoneColor.id == Fab.stone_color_id, isouter=True)
        .join(StoneThickness, StoneThickness.id == Fab.stone_thickness_id, isouter=True)
        .join(Edge, Edge.id == Fab.edge_id, isouter=True)
        .where(
            ShopCutPlan.id == task_id,
            ShopCutPlan.workstation_id == workstation_id,
        )
        .limit(1)
    )

    task_row = (await db.execute(task_query)).first()
    if not task_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    plan = task_row[0]
    updated_start = _normalize_naive_dt(payload.actual_start_date) if payload.actual_start_date is not None else plan.actual_start_date
    updated_end = _normalize_naive_dt(payload.actual_end_date) if payload.actual_end_date is not None else plan.actual_end_date

    if updated_start and updated_end and updated_end < updated_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="actual_end_date cannot be earlier than actual_start_date",
        )

    if payload.work_percentage is not None:
        plan.work_percentage = payload.work_percentage
    if payload.actual_start_date is not None:
        plan.actual_start_date = updated_start
    if payload.actual_end_date is not None:
        plan.actual_end_date = updated_end
    if payload.notes is not None:
        plan.notes = payload.notes

    plan.updated_at = datetime.now()
    plan.updated_by = current_user.id

    await db.commit()
    await db.refresh(plan)

    job_id = task_row[2].id
    as_of = datetime.now().replace(second=0, microsecond=0)
    total_actual_hours, total_actual_seconds = await _recalculate_operator_job_work_totals(
        db=db,
        job_id=job_id,
        operator_id=operator_id,
        workstation_id=workstation_id,
        as_of=as_of,
    )

    active_session = await _get_active_operator_job_session(
        db,
        operator_id=operator_id,
        job_id=job_id,
        workstation_id=workstation_id,
    )

    task = _serialize_operator_workstation_task(
        task_row,
        operator=operator,
        total_actual_hours=total_actual_hours,
        total_actual_seconds=total_actual_seconds,
        run_time=_current_session_run_time(active_session, as_of) if active_session else None,
    )

    task["files"] = await _get_operator_task_files(
        db=db,
        operator_id=operator_id,
        task_id=task_id,
        base_url=FileService.get_base_url(request),
    )

    return success_response(task, "Task updated successfully")


@router.get("/{operator_id}/workstations/{workstation_id}/tasks/active")
async def get_active_workstation_task_by_operator(
    operator_id: int,
    workstation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the operator's currently active task for the selected workstation."""

    operator = (await db.execute(select(User).where(User.id == operator_id))).scalar_one_or_none()
    if not operator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operator not found")

    if not getattr(current_user, "is_super_admin", False) and current_user.id != operator_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this operator's tasks")

    workstation = (await db.execute(select(WorkStation).where(WorkStation.id == workstation_id))).scalar_one_or_none()
    if not workstation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workstation not found")

    if operator_id not in (workstation.operator_ids or []):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workstation is not assigned to this operator")

    active_session = await _get_active_operator_job_session(
        db,
        operator_id=operator_id,
        workstation_id=workstation_id,
    )

    if not active_session:
        return success_response(
            {
                "operator_id": operator_id,
                "workstation_id": workstation_id,
                "task": None,
            },
            "No active task found",
        )

    task_query = (
        select(
            ShopCutPlan,
            Fab,
            BusinessJob,
            Account.name.label("account_name"),
            WorkStation.name.label("workstation_name"),
            PlanningSection.plan_name.label("plan_name"),
            StoneType.name.label("stone_type_name"),
            StoneColor.name.label("stone_color_name"),
            StoneThickness.thickness.label("stone_thickness_value"),
            Edge.name.label("edge_name"),
        )
        .join(Fab, Fab.id == ShopCutPlan.fab_id)
        .join(BusinessJob, BusinessJob.id == Fab.job_id)
        .join(Account, Account.id == BusinessJob.account_id, isouter=True)
        .join(WorkStation, WorkStation.id == ShopCutPlan.workstation_id, isouter=True)
        .join(PlanningSection, PlanningSection.id == ShopCutPlan.planning_section_id, isouter=True)
        .join(StoneType, StoneType.id == Fab.stone_type_id, isouter=True)
        .join(StoneColor, StoneColor.id == Fab.stone_color_id, isouter=True)
        .join(StoneThickness, StoneThickness.id == Fab.stone_thickness_id, isouter=True)
        .join(Edge, Edge.id == Fab.edge_id, isouter=True)
        .where(
            ShopCutPlan.workstation_id == workstation_id,
            Fab.job_id == active_session.job_id,
        )
        .order_by(ShopCutPlan.scheduled_start_date.desc(), ShopCutPlan.id.desc())
        .limit(1)
    )

    task_row = (await db.execute(task_query)).first()
    if not task_row:
        return success_response(
            {
                "operator_id": operator_id,
                "workstation_id": workstation_id,
                "task": None,
                "timer_session": _serialize_operator_job_timer_session(active_session),
            },
            "No active task found",
        )

    total_actual_hours, total_actual_seconds = await _recalculate_operator_job_work_totals(
        db=db,
        job_id=active_session.job_id,
        operator_id=operator_id,
        workstation_id=workstation_id,
        as_of=datetime.now().replace(second=0, microsecond=0),
    )

    task = _serialize_operator_workstation_task(
        task_row,
        operator=operator,
        total_actual_hours=total_actual_hours,
        total_actual_seconds=total_actual_seconds,
        run_time=_current_session_run_time(active_session, datetime.now().replace(second=0, microsecond=0)),
    )

    return success_response(
        {
            "operator_id": operator_id,
            "operator_name": f"{operator.first_name} {operator.last_name}".strip() or operator.username,
            "workstation_id": workstation_id,
            "workstation_name": task.get("workstation_name"),
            "task": task,
            "timer_session": _serialize_operator_job_timer_session(active_session),
        },
        "Active task retrieved successfully",
    )


@router.get("/me/tasks", response_model=SuccessResponse[dict])
async def get_current_operator_tasks(
    view: str = "week",
    reference_date: Optional[date] = None,
    active_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return tasks assigned to the currently logged-in operator for day/week/month calendar views."""

    normalized_view = (view or "week").strip().lower()
    target_date = reference_date or date.today()
    range_start, range_end = _build_calendar_window(normalized_view, target_date)

    pending_shop_revision_exists = (
        sa_select(ShopRevision.id)
        .where(
            ShopRevision.fab_id == Fab.id,
            ShopRevision.revision_completed.is_(False),
        )
        .exists()
    )

    query = (
        select(
            ShopCutPlan,
            Fab,
            BusinessJob.name.label("job_name"),
            BusinessJob.job_number.label("job_number"),
            Account.name.label("account_name"),
            WorkStation.name.label("workstation_name"),
            PlanningSection.plan_name.label("planning_section_name"),
            pending_shop_revision_exists.label("has_pending_shop_revision"),
        )
        .join(Fab, Fab.id == ShopCutPlan.fab_id)
        .join(BusinessJob, BusinessJob.id == Fab.job_id)
        .join(Account, Account.id == BusinessJob.account_id, isouter=True)
        .join(WorkStation, WorkStation.id == ShopCutPlan.workstation_id, isouter=True)
        .join(PlanningSection, PlanningSection.id == ShopCutPlan.planning_section_id, isouter=True)
        .where(
            ShopCutPlan.user_id == current_user.id,
            ShopCutPlan.scheduled_start_date.is_not(None),
            ShopCutPlan.scheduled_start_date < range_end,
        )
        .order_by(ShopCutPlan.scheduled_start_date.asc(), ShopCutPlan.sequence.asc(), ShopCutPlan.id.asc())
    )

    result = await db.execute(query)
    rows = [row for row in result.all() if _task_overlaps_window(row[0], range_start, range_end)]
    if active_only:
        rows = [row for row in rows if _task_is_active(row[0])]
    total = len(rows)
    paginated_rows = rows[skip:skip + limit]
    timer_status_by_fab = await _get_timer_statuses_for_fabs(
        db,
        operator_id=current_user.id,
        fab_ids=[row[0].fab_id for row in paginated_rows],
    )
    active_timer_fab_count_result = await db.execute(
        select(func.count(func.distinct(OperatorJobTimerSession.fab_id))).where(
            OperatorJobTimerSession.operator_id == current_user.id,
            OperatorJobTimerSession.fab_id.is_not(None),
            OperatorJobTimerSession.status.in_(["running", "paused"]),
        )
    )
    active_timer_fab_count = int(active_timer_fab_count_result.scalar() or 0)
    tasks = [_serialize_operator_task(row, timer_status_by_fab) for row in paginated_rows]
    page = (skip // limit) + 1 if limit > 0 else 1

    return success_response(
        {
            "operator_id": current_user.id,
            "view": normalized_view,
            "reference_date": target_date.isoformat(),
            "range_start": range_start.isoformat(),
            "range_end": range_end.isoformat(),
            "total": total,
            "active_timer_fab_count": active_timer_fab_count,
            "page": page,
            "per_page": limit,
            "data": tasks,
        },
        "Operator tasks retrieved successfully",
    )


async def _process_current_operator_job_timer_action(
    *,
    job_id: int,
    fab_id: Optional[int],
    action: str,
    db: AsyncSession,
    current_user: User,
    note: Optional[str] = None,
    workstation_id: Optional[int] = None,
):
    """Shared timer-action engine for start, pause, resume, and stop."""

    try:
        operator_id = current_user.id
        if operator_id is None:
            raise HTTPException(status_code=403, detail="Invalid operator context")

        normalized_action = (action or "").strip().lower()
        if normalized_action not in {"start", "pause", "resume", "stop"}:
            raise HTTPException(status_code=400, detail="action must be one of: start, pause, resume, stop")

        # Always use server-generated time — never trust client-supplied timestamps
        # for duration calculations, as timezone mismatches or stale values produce
        # incorrect elapsed-time results.
        action_ts: datetime = datetime.utcnow()

        job_result = await db.execute(select(BusinessJob).where(BusinessJob.id == job_id))
        job = job_result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")

        if workstation_id is not None:
            workstation_result = await db.execute(select(WorkStation).where(WorkStation.id == workstation_id))
            workstation = workstation_result.scalar_one_or_none()
            if not workstation:
                raise HTTPException(status_code=404, detail=f"Workstation with ID {workstation_id} not found")
            if operator_id not in (workstation.operator_ids or []):
                raise HTTPException(status_code=400, detail="Workstation is not assigned to this operator")

        if normalized_action in {"start", "stop"} and fab_id is not None:
            await assert_no_pending_shop_revision(db, fab_id)

        active_session = await _get_active_operator_job_session(
            db,
            operator_id=operator_id,
            fab_id=fab_id,
            job_id=job_id,
        )
        if normalized_action == "start":
            if active_session:
                raise HTTPException(status_code=400, detail="An active timer session already exists for this job")

            # Prevent starting if any running timer exists across all session types
            if not getattr(current_user, "is_super_admin", False):
                await assert_no_active_timer_session(db, operator_id)

            session = OperatorJobTimerSession(
                job_id=job_id,
                fab_id=fab_id,
                operator_id=operator_id,
                workstation_id=workstation_id,
                status="running",
                session_start_at=action_ts,
                current_run_start_at=action_ts,
                total_work_seconds=0,
                total_pause_seconds=0,
                created_at=datetime.now(),
                created_by=operator_id,
            )
            db.add(session)
            await db.flush()

            db.add(
                OperatorJobTimerEvent(
                    session_id=session.id,
                    job_id=job_id,
                    fab_id=fab_id,
                    operator_id=operator_id,
                    workstation_id=workstation_id,
                    action="start",
                    event_at=action_ts,
                    note=note,
                )
            )

            target_session = session

        elif normalized_action == "pause":
            if not active_session or active_session.status != "running":
                raise HTTPException(status_code=400, detail="No running timer session found to pause")

            run_start = _normalize_naive_dt(active_session.current_run_start_at)
            if not run_start:
                raise HTTPException(status_code=400, detail="Timer session is missing current_run_start_at")

            elapsed = int(max(0, (action_ts - run_start).total_seconds()))
            active_session.total_work_seconds = int(active_session.total_work_seconds or 0) + elapsed
            active_session.status = "paused"
            active_session.current_run_start_at = None
            active_session.current_pause_start_at = action_ts
            active_session.updated_at = datetime.now()
            active_session.updated_by = operator_id
            if workstation_id is not None:
                active_session.workstation_id = workstation_id

            db.add(
                OperatorJobTimerEvent(
                    session_id=active_session.id,
                    job_id=job_id,
                    fab_id=fab_id,
                    operator_id=operator_id,
                    workstation_id=workstation_id or active_session.workstation_id,
                    action="pause",
                    event_at=action_ts,
                    note=note,
                )
            )

            target_session = active_session

        elif normalized_action == "resume":
            if not active_session or active_session.status != "paused":
                raise HTTPException(status_code=400, detail="No paused timer session found to resume")

            if not getattr(current_user, "is_super_admin", False):
                await assert_no_active_timer_session(db, operator_id)

            pause_start = _normalize_naive_dt(active_session.current_pause_start_at)
            if pause_start and action_ts > pause_start:
                pause_elapsed = int((action_ts - pause_start).total_seconds())
                active_session.total_pause_seconds = int(active_session.total_pause_seconds or 0) + max(0, pause_elapsed)

            active_session.status = "running"
            active_session.current_pause_start_at = None
            active_session.current_run_start_at = action_ts
            active_session.updated_at = datetime.now()
            active_session.updated_by = operator_id
            if workstation_id is not None:
                active_session.workstation_id = workstation_id

            db.add(
                OperatorJobTimerEvent(
                    session_id=active_session.id,
                    job_id=job_id,
                    fab_id=fab_id,
                    operator_id=operator_id,
                    workstation_id=workstation_id or active_session.workstation_id,
                    action="resume",
                    event_at=action_ts,
                    note=note,
                )
            )

            target_session = active_session

        else:
            if not active_session or active_session.status not in {"running", "paused"}:
                raise HTTPException(status_code=400, detail="No active timer session found to stop")

            if active_session.status == "running":
                run_start = _normalize_naive_dt(active_session.current_run_start_at)
                if run_start and action_ts > run_start:
                    elapsed = int((action_ts - run_start).total_seconds())
                    active_session.total_work_seconds = int(active_session.total_work_seconds or 0) + max(0, elapsed)

            if active_session.status == "paused":
                pause_start = _normalize_naive_dt(active_session.current_pause_start_at)
                if pause_start and action_ts > pause_start:
                    pause_elapsed = int((action_ts - pause_start).total_seconds())
                    active_session.total_pause_seconds = int(active_session.total_pause_seconds or 0) + max(0, pause_elapsed)

            if workstation_id is not None:
                active_session.workstation_id = workstation_id
            active_session.status = "stopped"
            active_session.current_run_start_at = None
            active_session.current_pause_start_at = None
            active_session.stopped_at = action_ts
            active_session.updated_at = datetime.now()
            active_session.updated_by = operator_id

            db.add(
                OperatorJobTimerEvent(
                    session_id=active_session.id,
                    job_id=job_id,
                    fab_id=fab_id,
                    operator_id=operator_id,
                    workstation_id=workstation_id or active_session.workstation_id,
                    action="stop",
                    event_at=action_ts,
                    note=note,
                )
            )

            target_session = active_session

        # Flush pending ORM changes so the subsequent sum query reads the
        # updated total_work_seconds written above, not the stale DB value.
        await db.flush()

        total_actual_hours, total_actual_seconds = await _recalculate_operator_job_work_totals(
            db=db,
            fab_id=fab_id,
            job_id=job_id,
            operator_id=operator_id,
            as_of=action_ts,
        )

        await db.commit()
        if target_session.id:
            await db.refresh(target_session)

        return success_response(
            {
                "fab_id": fab_id,
                "job_id": job_id,
                "operator_id": operator_id,
                "workstation_id": target_session.workstation_id,
                "action": normalized_action,
                "timestamp": action_ts.isoformat(),
                "session": _serialize_operator_job_timer_session(target_session),
                "total_actual_seconds": total_actual_seconds,
                "total_actual_hours": total_actual_hours,
            },
            f"Timer {normalized_action} successful",
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process timer action: {str(exc)}")


async def _get_fab_and_job_id(db: AsyncSession, fab_id: int) -> tuple[Fab, int]:
    fab_result = await db.execute(select(Fab).where(Fab.id == fab_id))
    fab = fab_result.scalar_one_or_none()
    if not fab:
        raise HTTPException(status_code=404, detail=f"FAB with ID {fab_id} not found")

    job_id = fab.job_id
    if job_id is None:
        raise HTTPException(status_code=400, detail=f"FAB {fab_id} is not linked to a job")

    return fab, job_id


@router.post("/me/jobs/{fab_id}/timer/action", response_model=SuccessResponse[dict])
async def manage_current_operator_job_timer(
    fab_id: int,
    payload: OperatorJobTimerActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start, pause, resume, or stop a timer for the current operator on a FAB."""

    _, job_id = await _get_fab_and_job_id(db, fab_id)

    return await _process_current_operator_job_timer_action(
        job_id=job_id,
        fab_id=fab_id,
        action=payload.action,
        note=payload.note,
        workstation_id=payload.workstation_id,
        db=db,
        current_user=current_user,
    )


@router.post("/me/jobs/{fab_id}/timer/start", response_model=SuccessResponse[dict])
async def start_current_operator_job_timer(
    fab_id: int,
    payload: OperatorJobTimerCommandRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a timer for the current operator on a FAB."""

    _, job_id = await _get_fab_and_job_id(db, fab_id)

    return await _process_current_operator_job_timer_action(
        job_id=job_id,
        fab_id=fab_id,
        action="start",
        note=payload.note,
        workstation_id=payload.workstation_id,
        db=db,
        current_user=current_user,
    )


@router.post("/me/jobs/{fab_id}/timer/pause", response_model=SuccessResponse[dict])
async def pause_current_operator_job_timer(
    fab_id: int,
    payload: OperatorJobTimerCommandRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pause a running timer for the current operator on a FAB."""

    _, job_id = await _get_fab_and_job_id(db, fab_id)

    return await _process_current_operator_job_timer_action(
        job_id=job_id,
        fab_id=fab_id,
        action="pause",
        note=payload.note,
        workstation_id=payload.workstation_id,
        db=db,
        current_user=current_user,
    )


@router.post("/me/jobs/{fab_id}/timer/resume", response_model=SuccessResponse[dict])
async def resume_current_operator_job_timer(
    fab_id: int,
    payload: OperatorJobTimerCommandRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resume a paused timer for the current operator on a FAB."""

    _, job_id = await _get_fab_and_job_id(db, fab_id)

    return await _process_current_operator_job_timer_action(
        job_id=job_id,
        fab_id=fab_id,
        action="resume",
        note=payload.note,
        workstation_id=payload.workstation_id,
        db=db,
        current_user=current_user,
    )


@router.post("/me/jobs/{fab_id}/timer/stop", response_model=SuccessResponse[dict])
async def stop_current_operator_job_timer(
    fab_id: int,
    payload: OperatorJobTimerCommandRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stop an active timer for the current operator on a FAB."""

    _, job_id = await _get_fab_and_job_id(db, fab_id)

    return await _process_current_operator_job_timer_action(
        job_id=job_id,
        fab_id=fab_id,
        action="stop",
        note=payload.note,
        workstation_id=payload.workstation_id,
        db=db,
        current_user=current_user,
    )


@router.get("/me/jobs/{fab_id}/timer", response_model=SuccessResponse[dict])
async def get_current_operator_job_timer_state(
    fab_id: int,
    workstation_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current timer state for the logged-in operator on a FAB."""

    operator_id = current_user.id
    if operator_id is None:
        raise HTTPException(status_code=403, detail="Invalid operator context")

    _, job_id = await _get_fab_and_job_id(db, fab_id)

    timer_filters = [
        or_(
            OperatorJobTimerSession.fab_id == fab_id,
            (OperatorJobTimerSession.fab_id.is_(None)) & (OperatorJobTimerSession.job_id == job_id),
        ),
        OperatorJobTimerSession.operator_id == operator_id,
    ]
    if workstation_id is not None:
        timer_filters.append(OperatorJobTimerSession.workstation_id == workstation_id)

    latest_result = await db.execute(
        select(OperatorJobTimerSession)
        .where(*timer_filters)
        .order_by(OperatorJobTimerSession.created_at.desc())
        .limit(1)
    )
    latest = latest_result.scalars().first()

    now_ts = datetime.now().replace(second=0, microsecond=0)
    total_actual_hours, total_actual_seconds = await _recalculate_operator_job_work_totals(
        db=db,
        fab_id=fab_id,
        job_id=job_id,
        operator_id=operator_id,
        as_of=now_ts,
    )

    return success_response(
        {
            "fab_id": fab_id,
            "job_id": job_id,
            "operator_id": operator_id,
            "workstation_id": latest.workstation_id if latest else None,
            "session": _serialize_operator_job_timer_session(latest) if latest else None,
            "total_actual_seconds": total_actual_seconds,
            "total_actual_hours": total_actual_hours,
        },
        "Operator job timer state retrieved successfully",
    )


@router.get("/me/jobs/{fab_id}/timer/history", response_model=SuccessResponse[dict])
async def get_current_operator_job_timer_history(
    fab_id: int,
    workstation_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get timer session and event history for the logged-in operator on a FAB."""

    operator_id = current_user.id
    if operator_id is None:
        raise HTTPException(status_code=403, detail="Invalid operator context")

    _, job_id = await _get_fab_and_job_id(db, fab_id)

    session_filters = [
        or_(
            OperatorJobTimerSession.fab_id == fab_id,
            (OperatorJobTimerSession.fab_id.is_(None)) & (OperatorJobTimerSession.job_id == job_id),
        ),
        OperatorJobTimerSession.operator_id == operator_id,
    ]
    event_filters = [
        or_(
            OperatorJobTimerEvent.fab_id == fab_id,
            (OperatorJobTimerEvent.fab_id.is_(None)) & (OperatorJobTimerEvent.job_id == job_id),
        ),
        OperatorJobTimerEvent.operator_id == operator_id,
    ]
    if workstation_id is not None:
        session_filters.append(OperatorJobTimerSession.workstation_id == workstation_id)
        event_filters.append(OperatorJobTimerEvent.workstation_id == workstation_id)

    sessions_result = await db.execute(
        select(OperatorJobTimerSession)
        .where(*session_filters)
        .order_by(OperatorJobTimerSession.created_at.asc())
    )
    sessions = sessions_result.scalars().all()

    events_result = await db.execute(
        select(OperatorJobTimerEvent)
        .where(*event_filters)
        .order_by(OperatorJobTimerEvent.event_at.asc())
    )
    events = events_result.scalars().all()

    return success_response(
        {
            "fab_id": fab_id,
            "job_id": job_id,
            "operator_id": operator_id,
            "sessions": [_serialize_operator_job_timer_session(session) for session in sessions],
            "events": [_serialize_operator_job_timer_event(event) for event in events],
        },
        "Operator job timer history retrieved successfully",
    )


@router.post(
    "/{operator_id}/jobs/{fab_id}/upload",
    response_model=SuccessResponse[dict],
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["file"],
                        "properties": {
                            "file": {"type": "string", "format": "binary"},
                            "file_design": {"type": "string"},
                            "stage_name": {"type": "string"},
                            "file_type": {"type": "string"},
                            "directory": {"type": "string"},
                            "task_id": {"type": "integer"},
                        },
                    }
                }
            },
            "required": True,
        }
    },
)
async def upload_operator_job_qa_file(
    operator_id: int,
    fab_id: int,
    request: Request,
    file: UploadFile = FileUpload(...),
    file_design: str = Form("qa"),
    stage_name: str = Form("qa"),
    file_type: Optional[str] = Form(None),
    directory: Optional[str] = Form(None),
    task_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a QA file for a specific operator and FAB."""

    operator_result = await db.execute(select(User).where(User.id == operator_id))
    operator = operator_result.scalar_one_or_none()
    if not operator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operator not found")

    _, job_id = await _get_fab_and_job_id(db, fab_id)

    # Prevent spoofed uploads for another operator unless super admin.
    if not getattr(current_user, "is_super_admin", False) and current_user.id != operator_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload files for this operator",
        )

    if task_id is not None:
        task_result = await db.execute(
            select(ShopCutPlan)
            .join(Fab, Fab.id == ShopCutPlan.fab_id)
            .where(
                ShopCutPlan.id == task_id,
                ShopCutPlan.user_id == operator_id,
                Fab.id == fab_id,
            )
        )
        task = task_result.scalar_one_or_none()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found for this operator and FAB",
            )

    settings = get_settings()

    # Check file size in chunks, then rewind.
    file_size = 0
    chunk_size = 1024 * 1024
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        file_size += len(chunk)
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE} bytes",
            )
    await file.seek(0)

    # Validate extension against configured allow-list.
    if file.filename:
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else None
        if ext and ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension not allowed. Allowed extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}",
            )

    upload_directory = directory or f"uploads/fabs/{fab_id}/qa"

    resolved_file_type = file_type or "qa"

    file_data = await FileService.upload_file(
        db=db,
        file=file,
        user_id=operator_id,
        directory=upload_directory,
        file_type=resolved_file_type,
        file_design=file_design,
        stage_name=stage_name,
        job_id=job_id,
        fab_id=fab_id,
        task_id=task_id,
        request=request,
    )

    return success_response(
        {
            **file_data,
            "fab_id": fab_id,
            "job_id": job_id,
            "task_id": task_id,
            "operator_id": operator_id,
        },
        "QA file uploaded successfully",
    )


@router.get("/me/files", response_model=SuccessResponse[dict])
async def get_my_uploaded_files(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all files uploaded by the current operator across all jobs."""

    operator_id = current_user.id
    if operator_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")

    return await _get_operator_uploaded_files_response(
        operator_id=operator_id,
        request=request,
        db=db,
    )


@router.get("/{operator_id}/files", response_model=SuccessResponse[dict])
async def get_operator_uploaded_files(
    operator_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all files uploaded by a specific operator across all jobs."""

    operator_result = await db.execute(select(User).where(User.id == operator_id))
    operator = operator_result.scalar_one_or_none()
    if not operator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operator not found")

    if not getattr(current_user, "is_super_admin", False) and current_user.id != operator_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access files for this operator",
        )

    return await _get_operator_uploaded_files_response(
        operator_id=operator_id,
        request=request,
        db=db,
    )


async def _get_operator_uploaded_files_response(
    *,
    operator_id: int,
    request: Request,
    db: AsyncSession,
):
    file_result = await db.execute(
        select(File)
        .where(File.uploaded_by == operator_id)
        .order_by(File.created_at.desc(), File.id.desc())
    )
    files = file_result.scalars().all()
    base_url = FileService.get_base_url(request)

    return success_response(
        {
            "data": [_serialize_operator_file(file, base_url, operator_id) for file in files],
        },
        f"Retrieved {len(files)} file(s) uploaded by operator {operator_id}",
    )


@router.get("/{operator_id}/jobs/{fab_id}/files/{file_id}/view", response_model=SuccessResponse[dict])
async def view_operator_job_document(
    operator_id: int,
    fab_id: int,
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a viewable file URL for operator FAB documents."""

    operator_result = await db.execute(select(User).where(User.id == operator_id))
    operator = operator_result.scalar_one_or_none()
    if not operator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operator not found")

    if not getattr(current_user, "is_super_admin", False) and current_user.id != operator_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access files for this operator",
        )

    _, job_id = await _get_fab_and_job_id(db, fab_id)

    file_result = await db.execute(
        select(File)
        .outerjoin(ShopCutPlan, ShopCutPlan.id == File.task_id)
        .where(
            File.id == file_id,
            or_(
                File.fab_id == fab_id,
                (File.fab_id.is_(None)) & (File.job_id == job_id),
            ),
            File.uploaded_by == operator_id,
            or_(File.task_id.is_(None), ShopCutPlan.fab_id == fab_id),
        )
    )
    db_file = file_result.scalar_one_or_none()
    if not db_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    allowed_image_exts = {"jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff"}
    allowed_mime_prefixes = ("image/",)
    allowed_mime_exact = {"application/pdf"}

    filename = db_file.name or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    guessed_mime, _ = mimetypes.guess_type(filename)
    mime_type = guessed_mime or db_file.file_type or "application/octet-stream"

    is_allowed = (
        ext == "pdf"
        or ext in allowed_image_exts
        or mime_type in allowed_mime_exact
        or any(mime_type.startswith(prefix) for prefix in allowed_mime_prefixes)
    )
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF and image files are supported for browser viewing",
        )

    # Return JSON response with viewable file URL
    settings = get_settings()
    base_url = settings.API_BASE_URL
    
    return success_response(
        {
            "file_id": db_file.id,
            "file_name": db_file.name,
            "file_type": db_file.file_type,
            "file_size": db_file.file_size,
            "file_url": f"{base_url}/api/v1/files/{db_file.id}/view",
            "fab_id": fab_id,
            "job_id": job_id,
            "operator_id": operator_id,
        },
        "File URL retrieved successfully",
    )
