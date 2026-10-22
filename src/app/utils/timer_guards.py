"""Cross-endpoint active-timer guard.

Checks all DB-backed timer session tables to ensure a user does not already
have a running timer session before starting or resuming another.

Usage in route handlers (skip for super admins):

    if not getattr(current_user, "is_super_admin", False):
        await assert_no_active_timer_session(db, user_id)
"""

from collections import defaultdict

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.database.business_job import BusinessJob
from src.app.database.cnc import CNCDraftingSession
from src.app.database.drafting import DraftingSession
from src.app.database.fab import Fab
from src.app.database.final_programming import FinalProgrammingSession
from src.app.database.installer_job_timer_session import InstallerJobTimerSession
from src.app.database.operator_job_timer_session import OperatorJobTimerSession
from src.app.database.shop_cut_plan_timer_session import ShopCutPlanTimerSession
from src.app.database.slab_smith import SlabSmithSession
from src.app.database.templater_job_timer_session import TemplaterJobTimerSession
from src.app.database.user import User
from src.app.interface.generated_schemas import ShopRevision


def _is_blocking_timer_status(status_column):
    return or_(
        status_column.is_(None),
        status_column.not_in(["completed", "paused", "stopped"]),
    )


def _format_reference_ids(label: str, values: list[int]) -> str:
    unique_values = sorted({value for value in values if value is not None})
    if not unique_values:
        return ""

    joined_values = ", ".join(str(value) for value in unique_values[:5])
    if len(unique_values) > 5:
        joined_values = f"{joined_values}, +{len(unique_values) - 5} more"

    return f"{label} {joined_values}"


def _build_open_timer_message(timer_entries: list[dict[str, object]]) -> str:
    grouped_entries: dict[str, dict[str, list[int]]] = defaultdict(
        lambda: {"fab_ids": [], "job_ids": [], "plan_ids": []}
    )

    for entry in timer_entries:
        section = str(entry["section"])
        if entry.get("fab_id") is not None:
            grouped_entries[section]["fab_ids"].append(int(entry["fab_id"]))
        if entry.get("job_id") is not None:
            grouped_entries[section]["job_ids"].append(int(entry["job_id"]))
        if entry.get("plan_id") is not None:
            grouped_entries[section]["plan_ids"].append(int(entry["plan_id"]))

    summaries: list[str] = []
    for section, refs in grouped_entries.items():
        parts = [
            formatted
            for formatted in (
                _format_reference_ids("FABs", refs["fab_ids"]),
                _format_reference_ids("jobs", refs["job_ids"]),
                _format_reference_ids("plans", refs["plan_ids"]),
            )
            if formatted
        ]
        summaries.append(f"{section} ({'; '.join(parts)})" if parts else section)

    timers_text = "; ".join(summaries)
    return (
        "You already have open timers. "
        "End them before starting or resuming another one. "
        f"Open in: {timers_text}"
    )


async def assert_no_active_timer_session(db: AsyncSession, user_id: int) -> None:
    """Raise HTTP 409 if *user_id* already has an open timer in any DB-backed
    session table.

    Does NOT apply super-admin logic — callers are responsible for skipping
    this call when ``current_user.is_super_admin`` is True.
    """

    timer_entries: list[dict[str, object]] = []

    drafting_rows = (
        await db.execute(
            select(DraftingSession.fab_id, DraftingSession.status)
            .where(
                DraftingSession.drafter_id == user_id,
                _is_blocking_timer_status(DraftingSession.status),
            )
        )
    ).all()
    timer_entries.extend(
        [{"section": "Drafting", "fab_id": fab_id} for fab_id, _status_value in drafting_rows]
    )

    cnc_rows = (
        await db.execute(
            select(CNCDraftingSession.fab_id, CNCDraftingSession.status)
            .where(
                CNCDraftingSession.drafter_id == user_id,
                _is_blocking_timer_status(CNCDraftingSession.status),
            )
        )
    ).all()
    timer_entries.extend(
        [{"section": "CNC", "fab_id": fab_id} for fab_id, _status_value in cnc_rows]
    )

    final_programming_rows = (
        await db.execute(
            select(FinalProgrammingSession.fab_id, FinalProgrammingSession.status)
            .where(
                FinalProgrammingSession.user_id == user_id,
                _is_blocking_timer_status(FinalProgrammingSession.status),
            )
        )
    ).all()
    timer_entries.extend(
        [{"section": "Final Programming", "fab_id": fab_id} for fab_id, _status_value in final_programming_rows]
    )

    slab_smith_rows = (
        await db.execute(
            select(SlabSmithSession.fab_id, SlabSmithSession.status)
            .where(
                SlabSmithSession.user_id == user_id,
                _is_blocking_timer_status(SlabSmithSession.status),
            )
        )
    ).all()
    timer_entries.extend(
        [{"section": "SlabSmith", "fab_id": fab_id} for fab_id, _status_value in slab_smith_rows]
    )

    operator_rows = (
        await db.execute(
            select(OperatorJobTimerSession.job_id, OperatorJobTimerSession.fab_id, OperatorJobTimerSession.status)
            .where(
                OperatorJobTimerSession.operator_id == user_id,
                _is_blocking_timer_status(OperatorJobTimerSession.status),
            )
        )
    ).all()
    timer_entries.extend(
        [
            {"section": "Operator Job Timer", "job_id": job_id, "fab_id": fab_id}
            for job_id, fab_id, _status_value in operator_rows
        ]
    )

    shop_plan_rows = (
        await db.execute(
            select(ShopCutPlanTimerSession.shop_cut_plan_id, ShopCutPlanTimerSession.status)
            .where(
                ShopCutPlanTimerSession.operator_id == user_id,
                _is_blocking_timer_status(ShopCutPlanTimerSession.status),
            )
        )
    ).all()
    timer_entries.extend(
        [{"section": "Shop Cut Plan", "plan_id": plan_id} for plan_id, _status_value in shop_plan_rows]
    )

    installer_rows = (
        await db.execute(
            select(InstallerJobTimerSession.job_id, InstallerJobTimerSession.fab_id, InstallerJobTimerSession.status)
            .where(
                InstallerJobTimerSession.installer_id == user_id,
                _is_blocking_timer_status(InstallerJobTimerSession.status),
            )
        )
    ).all()
    timer_entries.extend(
        [
            {"section": "Installer Job Timer", "job_id": job_id, "fab_id": fab_id}
            for job_id, fab_id, _status_value in installer_rows
        ]
    )

    templater_rows = (
        await db.execute(
            select(TemplaterJobTimerSession.job_id, TemplaterJobTimerSession.fab_id, TemplaterJobTimerSession.status)
            .where(
                TemplaterJobTimerSession.templater_id == user_id,
                _is_blocking_timer_status(TemplaterJobTimerSession.status),
            )
        )
    ).all()
    timer_entries.extend(
        [
            {"section": "Templater Job Timer", "job_id": job_id, "fab_id": fab_id}
            for job_id, fab_id, _status_value in templater_rows
        ]
    )

    if timer_entries:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_build_open_timer_message(timer_entries),
        )


async def assert_no_pending_shop_revision(db: AsyncSession, fab_id: int) -> None:
    """Raise HTTP 409 if a FAB has any pending shop revision."""
    if fab_id is None:
        return

    pending_revision = (
        await db.execute(
            select(ShopRevision)
            .where(
                ShopRevision.fab_id == fab_id,
                ShopRevision.revision_completed.is_(False),
            )
            .order_by(ShopRevision.created_at.desc(), ShopRevision.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if pending_revision:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"FAB #{fab_id} has a pending shop revision. "
                "Complete the revision before starting or stopping an operator timer."
            ),
        )


# Desk-stage timers that lock a FAB's assignment while running:
# key -> (label, session model, column holding the person running it, running status)
_RUNNING_FAB_TIMER_SOURCES = {
    "drafting": ("Drafting", DraftingSession, DraftingSession.drafter_id, "drafting"),
    "cnc": ("CNC Programming", CNCDraftingSession, CNCDraftingSession.drafter_id, "drafting"),
    "final_programming": ("Final Programming", FinalProgrammingSession, FinalProgrammingSession.user_id, "active"),
    "slabsmith": ("SlabSmith", SlabSmithSession, SlabSmithSession.user_id, "active"),
}


def _person_name(first_name, last_name, username, user_id) -> str:
    full_name = f"{first_name or ''} {last_name or ''}".strip()
    return full_name or username or f"User #{user_id}"


async def assert_no_running_timer_for_reassignment(
    db: AsyncSession,
    fab_ids,
    sections,
    new_assignee_id=None,
    labels=None,
) -> None:
    """Raise HTTP 409 if any of *fab_ids* has a running timer in *sections*.

    A FAB can't be reassigned while someone is timing it; the message names who is running
    the timer so it can be stopped first. Paused/on-hold timers don't block, and neither does
    a timer run by *new_assignee_id* (reassigning to the same person is a no-op).
    *labels* overrides a section's display name, e.g. {"drafting": "Revision"}.
    """
    fab_ids = sorted({int(fab_id) for fab_id in fab_ids if fab_id is not None})
    if not fab_ids:
        return

    running: list[str] = []
    for key in sections:
        label, model, user_column, running_status = _RUNNING_FAB_TIMER_SOURCES[key]
        label = (labels or {}).get(key, label)
        query = (
            select(model.fab_id, user_column, User.first_name, User.last_name, User.username)
            .outerjoin(User, User.id == user_column)
            .where(model.fab_id.in_(fab_ids), model.status == running_status)
            .order_by(model.fab_id)
        )
        if new_assignee_id is not None:
            query = query.where(user_column != new_assignee_id)
        for fab_id, user_id, first_name, last_name, username in (await db.execute(query)).all():
            running.append(
                f"FAB #{fab_id} has a running {label} timer started by "
                f"{_person_name(first_name, last_name, username, user_id)}"
            )

    if running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{'; '.join(running)}. Stop the running timer before reassigning.",
        )
