from datetime import datetime, timedelta
import re
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import get_db
from src.app.database.audit_trail import AuditTrail
from src.app.database.business_job import BusinessJob
from src.app.database.fab import Fab
from src.app.database.user import User
from src.app.interface.response_wrappers import SuccessResponse
from src.app.middleware.jwt_auth import get_current_user
from src.app.utils.helpers import error_response, success_response


router = APIRouter(prefix="/audit-trails", tags=["Audit Trails"])


_FAB_RESOURCE_HINTS = {
    "fab",
    "fabs",
    "fab_details",
    "fab_notes",
    "templating",
    "drafting",
    "sales_ct",
    "cut_list",
    "final_programming",
    "wj_programming",
    "wj_scheduling",
    "resurface_scheduling",
    "install_scheduling",
    "install_completion",
    "revisions",
    "shop_revisions",
    "cost_of_stone",
    "cnc",
}

_JOB_RESOURCE_HINTS = {
    "job",
    "jobs",
    "business_jobs",
    "job_fab_listing",
    "job_timers",
    "job_extras",
}


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_id_from_payload(payload: Optional[dict[str, Any]], keys: list[str]) -> Optional[int]:
    if not isinstance(payload, dict):
        return None
    for key in keys:
        if key in payload:
            value = _to_int(payload.get(key))
            if value is not None:
                return value
    return None


def _extract_path_ids(path: Optional[str]) -> dict[str, Optional[int]]:
    if not path:
        return {"fab_id": None, "job_id": None, "employee_id": None}

    fab_match = re.search(r"/fabs/(\d+)", path)
    job_match = re.search(r"/(?:jobs|business-jobs|business_jobs)/(\d+)", path)
    employee_match = re.search(r"/employees/(\d+)", path)

    return {
        "fab_id": int(fab_match.group(1)) if fab_match else None,
        "job_id": int(job_match.group(1)) if job_match else None,
        "employee_id": int(employee_match.group(1)) if employee_match else None,
    }


def _infer_related_ids(audit: AuditTrail) -> dict[str, Optional[int]]:
    path_ids = _extract_path_ids(audit.request_path)

    resource_hint = (audit.resource_type or audit.activity_table_name or "").lower()
    fab_from_payload = (
        _extract_id_from_payload(audit.new_values, ["fab_id", "id"]) if resource_hint in _FAB_RESOURCE_HINTS else None
    )
    if fab_from_payload is None:
        fab_from_payload = _extract_id_from_payload(audit.old_values, ["fab_id", "id"]) if resource_hint in _FAB_RESOURCE_HINTS else None

    job_from_payload = (
        _extract_id_from_payload(audit.new_values, ["job_id", "id"]) if resource_hint in _JOB_RESOURCE_HINTS else None
    )
    if job_from_payload is None:
        job_from_payload = _extract_id_from_payload(audit.old_values, ["job_id", "id"]) if resource_hint in _JOB_RESOURCE_HINTS else None

    fab_id = path_ids["fab_id"] or fab_from_payload
    job_id = path_ids["job_id"] or job_from_payload

    if audit.record_id:
        if fab_id is None and resource_hint in _FAB_RESOURCE_HINTS:
            fab_id = audit.record_id
        if job_id is None and resource_hint in _JOB_RESOURCE_HINTS:
            job_id = audit.record_id

    # If job id is stored in a fab event payload, keep it as a secondary link.
    if job_id is None:
        job_id = _extract_id_from_payload(audit.new_values, ["job_id"]) or _extract_id_from_payload(
            audit.old_values, ["job_id"]
        )

    return {
        "fab_id": fab_id,
        "job_id": job_id,
        "employee_id": path_ids["employee_id"],
    }


def _user_payload(user: Optional[User]) -> Optional[dict[str, Any]]:
    if not user:
        return None
    return {
        "id": user.id,
        "username": user.username,
        "employee_id": str(user.employee_id) if user.employee_id else None,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": f"{user.first_name} {user.last_name}".strip(),
        "email": user.email,
        "department": user.department,
    }


def _fab_payload(fab: Optional[Fab]) -> Optional[dict[str, Any]]:
    if not fab:
        return None
    return {
        "id": fab.id,
        "job_id": fab.job_id,
        "fab_type": fab.fab_type,
        "current_stage": fab.current_stage,
        "status_id": fab.status_id,
    }


def _job_payload(job: Optional[BusinessJob]) -> Optional[dict[str, Any]]:
    if not job:
        return None
    return {
        "id": job.id,
        "name": job.name,
        "job_number": job.job_number,
        "status_id": job.status_id,
        "account_id": job.account_id,
    }


def _build_audit_item(
    audit: AuditTrail,
    actor: Optional[User],
    target_employee: Optional[User],
    fab: Optional[Fab],
    job: Optional[BusinessJob],
) -> dict[str, Any]:
    actor_name = None
    if actor:
        actor_name = f"{actor.first_name} {actor.last_name}".strip()

    return {
        "audit_id": audit.id,
        "timestamp": audit.created_at.isoformat() if audit.created_at else None,
        "operation": audit.operation,
        "resource_type": audit.resource_type,
        "table": audit.activity_table_name,
        "message": audit.activity_message,
        "request": {
            "method": audit.request_method,
            "path": audit.request_path,
            "status_code": audit.response_status_code,
            "device_id": audit.device_id,
            "ip_address": audit.ip_address,
            "browser": audit.browser,
        },
        "actor": _user_payload(actor),
        "linked_employee": _user_payload(target_employee),
        "linked_fab": _fab_payload(fab),
        "linked_job": _job_payload(job),
        "manipulated_data": {
            "record_id": audit.record_id,
            "changed_fields": audit.changed_fields,
            "old_values": audit.old_values,
            "new_values": audit.new_values,
        },
        "summary": {
            "performed_by": actor_name or "System",
            "did_what": audit.activity_message,
            "where": audit.request_path,
        },
    }


@router.get("", response_model=SuccessResponse[dict])
async def list_audit_trails(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    user_id: Optional[int] = Query(None, description="Filter by actor user id"),
    operation: Optional[str] = Query(None, description="Filter by operation (POST, PUT, DELETE, login, etc.)"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    job_id: Optional[int] = Query(None, description="Filter trails related to a specific job"),
    fab_id: Optional[int] = Query(None, description="Filter trails related to a specific FAB"),
    start_date: Optional[datetime] = Query(None, description="Filter trails created at or after this datetime"),
    end_date: Optional[datetime] = Query(None, description="Filter trails created at or before this datetime"),
    search: Optional[str] = Query(None, description="Search text in message/path/table"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    filters = []

    if user_id is not None:
        filters.append(AuditTrail.user_id == user_id)

    if operation:
        filters.append(AuditTrail.operation.ilike(f"%{operation.strip()}%"))

    if resource_type:
        filters.append(AuditTrail.resource_type.ilike(f"%{resource_type.strip()}%"))

    if start_date is not None:
        filters.append(AuditTrail.created_at >= start_date)

    if end_date is not None:
        filters.append(AuditTrail.created_at <= end_date)

    if search:
        search_term = f"%{search.strip()}%"
        filters.append(
            or_(
                AuditTrail.activity_message.ilike(search_term),
                AuditTrail.request_path.ilike(search_term),
                AuditTrail.activity_table_name.ilike(search_term),
            )
        )

    if fab_id is not None:
        filters.append(
            or_(
                AuditTrail.request_path.ilike(f"%/fabs/{fab_id}%"),
                and_(
                    AuditTrail.record_id == fab_id,
                    or_(
                        AuditTrail.resource_type.in_(list(_FAB_RESOURCE_HINTS)),
                        AuditTrail.activity_table_name.in_(list(_FAB_RESOURCE_HINTS)),
                    ),
                ),
            )
        )

    if job_id is not None:
        filters.append(
            or_(
                AuditTrail.request_path.ilike(f"%/jobs/{job_id}%"),
                AuditTrail.request_path.ilike(f"%/business-jobs/{job_id}%"),
                and_(
                    AuditTrail.record_id == job_id,
                    or_(
                        AuditTrail.resource_type.in_(list(_JOB_RESOURCE_HINTS)),
                        AuditTrail.activity_table_name.in_(list(_JOB_RESOURCE_HINTS)),
                    ),
                ),
            )
        )

    base_query = select(AuditTrail)
    if filters:
        base_query = base_query.where(and_(*filters))

    count_query = select(func.count()).select_from(base_query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(base_query.order_by(AuditTrail.created_at.desc()).offset(offset).limit(page_size))
    audits = result.scalars().all()

    actor_ids: set[int] = {audit.user_id for audit in audits if audit.user_id is not None}
    related = {audit.id: _infer_related_ids(audit) for audit in audits}

    fab_ids: set[int] = {ids["fab_id"] for ids in related.values() if ids.get("fab_id") is not None}
    job_ids: set[int] = {ids["job_id"] for ids in related.values() if ids.get("job_id") is not None}
    employee_ids: set[int] = {ids["employee_id"] for ids in related.values() if ids.get("employee_id") is not None}

    users_by_id: dict[int, User] = {}
    if actor_ids or employee_ids:
        all_user_ids = actor_ids.union(employee_ids)
        users_result = await db.execute(select(User).where(User.id.in_(all_user_ids)))
        users_by_id = {user.id: user for user in users_result.scalars().all() if user.id is not None}

    fabs_by_id: dict[int, Fab] = {}
    if fab_ids:
        fabs_result = await db.execute(select(Fab).where(Fab.id.in_(fab_ids)))
        fabs = fabs_result.scalars().all()
        fabs_by_id = {fab.id: fab for fab in fabs if fab.id is not None}
        job_ids.update({fab.job_id for fab in fabs if fab.job_id is not None})

    jobs_by_id: dict[int, BusinessJob] = {}
    if job_ids:
        jobs_result = await db.execute(select(BusinessJob).where(BusinessJob.id.in_(job_ids)))
        jobs_by_id = {job.id: job for job in jobs_result.scalars().all() if job.id is not None}

    records: list[dict[str, Any]] = []
    for audit in audits:
        ids = related.get(audit.id, {})
        linked_fab = fabs_by_id.get(ids.get("fab_id")) if ids.get("fab_id") else None

        linked_job = None
        if ids.get("job_id"):
            linked_job = jobs_by_id.get(ids["job_id"])
        if linked_job is None and linked_fab and linked_fab.job_id:
            linked_job = jobs_by_id.get(linked_fab.job_id)

        records.append(
            _build_audit_item(
                audit=audit,
                actor=users_by_id.get(audit.user_id),
                target_employee=users_by_id.get(ids.get("employee_id")),
                fab=linked_fab,
                job=linked_job,
            )
        )

    data = {
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
        "filters_applied": {
            "user_id": user_id,
            "operation": operation,
            "resource_type": resource_type,
            "job_id": job_id,
            "fab_id": fab_id,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "search": search,
        },
        "records": records,
        "requested_by": current_user.id,
    }

    return success_response(data, "Audit trails retrieved successfully")


@router.get("/summary", response_model=SuccessResponse[dict])
async def get_audit_summary(
    last_hours: int = Query(24, ge=1, le=24 * 30, description="Summarize over the last N hours"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    since = datetime.now() - timedelta(hours=last_hours)

    total_result = await db.execute(select(func.count(AuditTrail.id)).where(AuditTrail.created_at >= since))
    total = total_result.scalar() or 0

    operation_result = await db.execute(
        select(AuditTrail.operation, func.count(AuditTrail.id).label("count"))
        .where(AuditTrail.created_at >= since)
        .group_by(AuditTrail.operation)
        .order_by(func.count(AuditTrail.id).desc())
        .limit(10)
    )
    top_operations = [{"operation": row[0], "count": row[1]} for row in operation_result.all()]

    resource_result = await db.execute(
        select(AuditTrail.resource_type, func.count(AuditTrail.id).label("count"))
        .where(AuditTrail.created_at >= since)
        .group_by(AuditTrail.resource_type)
        .order_by(func.count(AuditTrail.id).desc())
        .limit(10)
    )
    top_resources = [{"resource_type": row[0], "count": row[1]} for row in resource_result.all()]

    active_user_result = await db.execute(
        select(AuditTrail.user_id, func.count(AuditTrail.id).label("count"))
        .where(and_(AuditTrail.created_at >= since, AuditTrail.user_id > 0))
        .group_by(AuditTrail.user_id)
        .order_by(func.count(AuditTrail.id).desc())
        .limit(10)
    )
    active_user_rows = active_user_result.all()

    active_user_ids = [row[0] for row in active_user_rows if row[0] is not None]
    users_by_id: dict[int, User] = {}
    if active_user_ids:
        users_result = await db.execute(select(User).where(User.id.in_(active_user_ids)))
        users_by_id = {user.id: user for user in users_result.scalars().all() if user.id is not None}

    top_users = []
    for user_id, count in active_user_rows:
        user = users_by_id.get(user_id)
        top_users.append(
            {
                "user_id": user_id,
                "count": count,
                "username": user.username if user else None,
                "full_name": f"{user.first_name} {user.last_name}".strip() if user else "Unknown",
                "employee_id": str(user.employee_id) if user and user.employee_id else None,
            }
        )

    data = {
        "window": {
            "last_hours": last_hours,
            "since": since.isoformat(),
            "until": datetime.now().isoformat(),
        },
        "total_events": total,
        "top_operations": top_operations,
        "top_resources": top_resources,
        "top_users": top_users,
        "requested_by": current_user.id,
    }
    return success_response(data, "Audit trail summary retrieved successfully")


@router.get("/{audit_id}", response_model=SuccessResponse[dict])
async def get_audit_trail_by_id(
    audit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    result = await db.execute(select(AuditTrail).where(AuditTrail.id == audit_id))
    audit = result.scalars().first()

    if not audit:
        return error_response(f"Audit trail {audit_id} not found", status_code=404)

    ids = _infer_related_ids(audit)

    actor = None
    if audit.user_id is not None:
        actor_result = await db.execute(select(User).where(User.id == audit.user_id))
        actor = actor_result.scalars().first()

    target_employee = None
    if ids.get("employee_id"):
        employee_result = await db.execute(select(User).where(User.id == ids["employee_id"]))
        target_employee = employee_result.scalars().first()

    fab = None
    if ids.get("fab_id"):
        fab_result = await db.execute(select(Fab).where(Fab.id == ids["fab_id"]))
        fab = fab_result.scalars().first()

    job = None
    if ids.get("job_id"):
        job_result = await db.execute(select(BusinessJob).where(BusinessJob.id == ids["job_id"]))
        job = job_result.scalars().first()
    elif fab and fab.job_id:
        job_result = await db.execute(select(BusinessJob).where(BusinessJob.id == fab.job_id))
        job = job_result.scalars().first()

    item = _build_audit_item(
        audit=audit,
        actor=actor,
        target_employee=target_employee,
        fab=fab,
        job=job,
    )
    item["requested_by"] = current_user.id

    return success_response(item, "Audit trail details retrieved successfully")