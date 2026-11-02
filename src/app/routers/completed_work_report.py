"""
Completed Work report: one report, one department at a time (CAD drafting first;
CNC, SlabSmith and Final Programming use the same shape). Each department says
where its completed records live, when they were completed, and who did them.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Callable, Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, false, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.app.database import get_db
from src.app.database.account import Account
from src.app.database.business_job import BusinessJob
from src.app.database.fab import Fab
from src.app.database.stone_color import StoneColor
from src.app.database.stone_type import StoneType
from src.app.database.user import User
from src.app.interface.generated_schemas import CNCDrafting, Drafting, FinalProgramming, SlabSmith
from src.app.middleware.jwt_auth import get_current_user
from src.app.utils.helpers import success_response, to_app_tz

router = APIRouter(prefix="/reports/completed-work", tags=["Reports"])


@dataclass(frozen=True)
class Department:
    label: str
    person_label: str
    model: type
    completed_on: Callable  # model -> SQL expression for the completion timestamp
    is_completed: Callable  # model -> SQL condition


def _done(model):
    return or_(model.is_completed.is_(True), model.status_id == 3)


DEPARTMENTS: dict[str, Department] = {
    "cad": Department(
        "CAD - Drafting", "Drafter", Drafting,
        lambda m: func.coalesce(m.drafter_end_date, Fab.draft_completed_date), _done,
    ),
    "cnc": Department("CNC Programming", "CNC Programmer", CNCDrafting, lambda m: m.drafter_end_date, _done),
    "slabsmith": Department(
        "SlabSmith", "SlabSmith Operator", SlabSmith,
        lambda m: func.coalesce(m.slabsmith_completed_date, m.end_date), _done,
    ),
    "final_programming": Department(
        "Final Programming", "Final Programmer", FinalProgramming, lambda m: m.drafter_end_date, _done,
    ),
}

DepartmentKey = Literal["cad", "cnc", "slabsmith", "final_programming"]
SearchType = Literal["fab_id", "job_name", "job_number", "account_name"]


def _search_condition(search: str, search_type: Optional[SearchType]):
    """Search FAB ID, job name, job number or account; one field when search_type is given."""
    term = f"%{search.strip()}%"
    fab_id = _int_or_none(search)
    by_field = {
        "fab_id": Fab.id == fab_id if fab_id is not None else false(),
        "job_name": BusinessJob.name.ilike(term),
        "job_number": BusinessJob.job_number.ilike(term),
        "account_name": Account.name.ilike(term),
    }
    if search_type:
        return by_field[search_type]
    return or_(*([by_field["fab_id"]] if fab_id is not None else []), *list(by_field.values())[1:])


def _int_or_none(value: str) -> Optional[int]:
    value = value.strip()
    return int(value) if value.isdigit() else None


@router.get("/departments")
async def list_departments(current_user: User = Depends(get_current_user)):
    return success_response(
        [{"key": key, "label": d.label, "person_label": d.person_label} for key, d in DEPARTMENTS.items()],
        "Departments retrieved",
    )


@router.get("")
async def completed_work_report(
    department: DepartmentKey = Query("cad"),
    start_date: Optional[date] = Query(None, description="Completed on or after (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Completed on or before (YYYY-MM-DD)"),
    employee_id: Optional[int] = Query(None, description="Who completed the work (drafter, programmer, operator)"),
    search: Optional[str] = Query(None),
    search_type: Optional[SearchType] = Query(None, description="Limit search to one field; default searches all"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dept = DEPARTMENTS[department]
    model = dept.model
    Person = aliased(User)
    completed_on = dept.completed_on(model).label("completed_on")

    conditions = [dept.is_completed(model)]
    if start_date:
        conditions.append(dept.completed_on(model) >= to_app_tz(datetime.combine(start_date, time.min)))
    if end_date:
        conditions.append(dept.completed_on(model) < to_app_tz(datetime.combine(end_date + timedelta(days=1), time.min)))
    if employee_id is not None:
        conditions.append(model.drafter_id == employee_id)
    if search and search.strip():
        conditions.append(_search_condition(search, search_type))

    base = (
        select(model.id)
        .select_from(model)
        .join(Fab, Fab.id == model.fab_id)
        .join(BusinessJob, BusinessJob.id == Fab.job_id, isouter=True)
        .join(Account, Account.id == BusinessJob.account_id, isouter=True)
        .where(and_(*conditions))
    )
    totals = (
        await db.execute(
            select(func.count(), func.coalesce(func.sum(Fab.total_sqft), 0))
            .select_from(model)
            .join(Fab, Fab.id == model.fab_id)
            .where(model.id.in_(base))
        )
    ).one()

    rows = (
        await db.execute(
            select(
                completed_on,
                Fab.id.label("fab_id"),
                Fab.fab_type,
                Fab.input_area,
                Fab.total_sqft,
                BusinessJob.job_number,
                BusinessJob.name.label("job_name"),
                Account.name.label("account_name"),
                StoneType.name.label("stone_type"),
                StoneColor.name.label("stone_color"),
                model.drafter_id.label("employee_id"),
                Person.first_name,
                Person.last_name,
            )
            .select_from(model)
            .join(Fab, Fab.id == model.fab_id)
            .join(BusinessJob, BusinessJob.id == Fab.job_id, isouter=True)
            .join(Account, Account.id == BusinessJob.account_id, isouter=True)
            .join(StoneType, StoneType.id == Fab.stone_type_id, isouter=True)
            .join(StoneColor, StoneColor.id == Fab.stone_color_id, isouter=True)
            .join(Person, Person.id == model.drafter_id, isouter=True)
            .where(model.id.in_(base))
            .order_by(dept.completed_on(model).desc().nullslast(), Fab.id.desc())
            .offset(skip)
            .limit(limit)
        )
    ).all()

    items = [
        {
            "completed_on": row.completed_on.isoformat() if row.completed_on else None,
            "fab_id": row.fab_id,
            "fab_type": row.fab_type,
            "job_number": row.job_number,
            "job_name": row.job_name,
            "account_name": row.account_name,
            "area": row.input_area,
            "stone_type": row.stone_type,
            "stone_color": row.stone_color,
            "sqft": float(row.total_sqft) if row.total_sqft is not None else None,
            "employee_id": row.employee_id,
            "employee_name": " ".join(p for p in (row.first_name, row.last_name) if p) or None,
        }
        for row in rows
    ]
    return success_response(
        {
            "department": department,
            "department_label": dept.label,
            "person_label": dept.person_label,
            "items": items,
            "total": totals[0],
            "total_sqft": float(totals[1] or 0),
        },
        "Completed work retrieved",
    )
