"""
Completed Work report: one report, one department at a time. Each department says
where its completed records live, when they were completed, and who did them.

Who did the work comes from the timer session that was running when the work was
completed, not from the record's current assignee: reassigning a FAB (e.g. to a
revisor) rewrites the assignee but must not re-credit work that was already done.
Work completed before the credited person had an account (Caspio-era data brought
over by the migration) is reported as legacy instead of being credited to anyone.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Callable, Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Select, false, func, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.app.database import get_db
from src.app.database.account import Account
from src.app.database.business_job import BusinessJob
from src.app.database.fab import Fab
from src.app.database.stone_color import StoneColor
from src.app.database.stone_type import StoneType
from src.app.database.user import User
from src.app.interface.generated_schemas import (
    CNCDrafting,
    Drafting,
    DraftingSession,
    FinalProgramming,
    FinalProgrammingSession,
    Revision,
    SlabSmith,
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.utils.helpers import success_response, to_app_tz

router = APIRouter(prefix="/reports/completed-work", tags=["Reports"])

# The placeholder user the Caspio migration put on every record it created.
MIGRATION_USERNAME = "migration_bot"
MIGRATION_EMAIL = "migration@localhost"
LEGACY_LABEL = "Legacy (Caspio)"


@dataclass(frozen=True)
class Department:
    label: str
    person_label: str
    # Returns a SELECT of (fab_id, completed_on, person_id), one row per completed piece of work.
    source: Callable[[], Select]


def _done(model):
    return or_(model.is_completed.is_(True), model.status_id == 3)


def _session_person(session_model, person_col, fab_id, completed_on, started_after=None):
    """Who ran the latest timer session on this FAB that started before the work was completed."""
    conditions = [session_model.fab_id == fab_id, session_model.session_start_time <= completed_on]
    if started_after is not None:
        conditions.append(session_model.session_start_time >= started_after)
    return (
        select(person_col)
        .where(*conditions)
        .order_by(session_model.session_start_time.desc(), session_model.id.desc())
        .limit(1)
        .scalar_subquery()
    )


def _cad_source():
    completed_on = func.coalesce(Drafting.drafter_end_date, Fab.draft_completed_date)
    person = func.coalesce(
        _session_person(DraftingSession, DraftingSession.drafter_id, Drafting.fab_id, completed_on),
        Drafting.drafter_id,
    )
    return (
        select(Drafting.fab_id, completed_on.label("completed_on"), person.label("person_id"))
        .select_from(Drafting)
        .join(Fab, Fab.id == Drafting.fab_id)
        .where(_done(Drafting))
    )


def _revisions_source():
    # Revision work is timed with drafting sessions started after the revision was requested.
    person = func.coalesce(
        _session_person(
            DraftingSession, DraftingSession.drafter_id, Revision.fab_id, Revision.actual_end_date,
            started_after=Revision.created_at,
        ),
        Revision.assigned_to,
        Revision.updated_by,
    )
    return (
        select(Revision.fab_id, Revision.actual_end_date.label("completed_on"), person.label("person_id"))
        .where(Revision.is_completed.is_(True), Revision.actual_end_date.isnot(None))
    )


def _cnc_source():
    return select(
        CNCDrafting.fab_id, CNCDrafting.drafter_end_date.label("completed_on"), CNCDrafting.drafter_id.label("person_id"),
    ).where(_done(CNCDrafting))


def _slabsmith_source():
    return select(
        SlabSmith.fab_id,
        func.coalesce(SlabSmith.slabsmith_completed_date, SlabSmith.end_date).label("completed_on"),
        SlabSmith.drafter_id.label("person_id"),
    ).where(_done(SlabSmith))


def _final_programming_source():
    # Completing Final Programming stamps the FAB; final_programmings only holds migrated rows.
    completed_on = Fab.final_programming_completed_date
    migrated_programmer = (
        select(FinalProgramming.drafter_id)
        .where(FinalProgramming.fab_id == Fab.id, FinalProgramming.drafter_end_date == completed_on)
        .limit(1)
        .scalar_subquery()
    )
    person = func.coalesce(
        _session_person(FinalProgrammingSession, FinalProgrammingSession.user_id, Fab.id, completed_on),
        migrated_programmer,
        Fab.drafter_id,  # set to the final programmer when they mark it complete
    )
    return (
        select(Fab.id.label("fab_id"), completed_on.label("completed_on"), person.label("person_id"))
        .where(Fab.final_programming_complete.is_(True), completed_on.isnot(None))
    )


DEPARTMENTS: dict[str, Department] = {
    "cad": Department("CAD - Drafting", "Drafter", _cad_source),
    "revisions": Department("CAD - Revisions", "Revisor", _revisions_source),
    "cnc": Department("CNC Programming", "CNC Programmer", _cnc_source),
    "slabsmith": Department("SlabSmith", "SlabSmith Operator", _slabsmith_source),
    "final_programming": Department("Final Programming", "Final Programmer", _final_programming_source),
}

DepartmentKey = Literal["cad", "revisions", "cnc", "slabsmith", "final_programming"]
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
    employee_id: Optional[int] = Query(None, description="Who completed the work (drafter, revisor, programmer, operator)"),
    search: Optional[str] = Query(None),
    search_type: Optional[SearchType] = Query(None, description="Limit search to one field; default searches all"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dept = DEPARTMENTS[department]
    work = dept.source().subquery("work")
    Person = aliased(User)
    is_legacy = or_(
        work.c.person_id.is_(None),
        Person.id.is_(None),
        Person.username == MIGRATION_USERNAME,
        Person.email == MIGRATION_EMAIL,
        Person.created_at > work.c.completed_on,  # credited to someone who didn't work here yet
    )

    conditions = []
    if start_date:
        conditions.append(work.c.completed_on >= to_app_tz(datetime.combine(start_date, time.min)))
    if end_date:
        conditions.append(work.c.completed_on < to_app_tz(datetime.combine(end_date + timedelta(days=1), time.min)))
    if employee_id is not None:
        conditions.extend([work.c.person_id == employee_id, not_(is_legacy)])
    if search and search.strip():
        conditions.append(_search_condition(search, search_type))

    def joined(query):
        return (
            query.select_from(work)
            .join(Fab, Fab.id == work.c.fab_id)
            .join(BusinessJob, BusinessJob.id == Fab.job_id, isouter=True)
            .join(Account, Account.id == BusinessJob.account_id, isouter=True)
            .join(Person, Person.id == work.c.person_id, isouter=True)
            .where(*conditions)
        )

    totals = (await db.execute(joined(select(func.count(), func.coalesce(func.sum(Fab.total_sqft), 0))))).one()

    rows = (
        await db.execute(
            joined(
                select(
                    work.c.completed_on,
                    Fab.id.label("fab_id"),
                    Fab.fab_type,
                    Fab.input_area,
                    Fab.total_sqft,
                    BusinessJob.job_number,
                    BusinessJob.name.label("job_name"),
                    Account.name.label("account_name"),
                    StoneType.name.label("stone_type"),
                    StoneColor.name.label("stone_color"),
                    work.c.person_id,
                    Person.first_name,
                    Person.last_name,
                    is_legacy.label("is_legacy"),
                )
            )
            .join(StoneType, StoneType.id == Fab.stone_type_id, isouter=True)
            .join(StoneColor, StoneColor.id == Fab.stone_color_id, isouter=True)
            .order_by(work.c.completed_on.desc().nullslast(), Fab.id.desc())
            .offset(skip)
            .limit(limit)
        )
    ).all()

    items = []
    for row in rows:
        legacy = bool(row.is_legacy)
        items.append(
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
                "employee_id": None if legacy else row.person_id,
                "employee_name": LEGACY_LABEL if legacy
                else (" ".join(p.strip() for p in (row.first_name, row.last_name) if p and p.strip()) or None),
                "is_legacy": legacy,
            }
        )
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
