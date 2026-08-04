"""Cross-endpoint active-timer guard.

Checks all DB-backed timer session tables to ensure a user does not already
have a running timer session before starting or resuming another.

Usage in route handlers (skip for super admins):

    if not getattr(current_user, "is_super_admin", False):
        await assert_no_active_timer_session(db, user_id)
"""

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
from src.app.interface.generated_schemas import ShopRevision


def _build_open_timer_message(timer_entries: list[str]) -> str:
    timers_text = "; ".join(timer_entries)
    return (
        "You already have open timer(s). "
        "Please end those timer(s) before starting or resuming another one. "
        f"Open timers: {timers_text}"
    )


async def assert_no_active_timer_session(db: AsyncSession, user_id: int) -> None:
    """Raise HTTP 409 if *user_id* already has an open timer in any DB-backed
    session table.

    Does NOT apply super-admin logic — callers are responsible for skipping
    this call when ``current_user.is_super_admin`` is True.
    """

    timer_entries: list[str] = []

    drafting_rows = (
        await db.execute(
            select(DraftingSession.fab_id, DraftingSession.status)
            .where(
                DraftingSession.drafter_id == user_id,
                or_(DraftingSession.status != "completed", DraftingSession.status.is_(None)),
            )
        )
    ).all()
    timer_entries.extend(
        [f"Drafting (FAB #{fab_id}, status: {status_value})" for fab_id, status_value in drafting_rows]
    )

    cnc_rows = (
        await db.execute(
            select(CNCDraftingSession.fab_id, CNCDraftingSession.status)
            .where(
                CNCDraftingSession.drafter_id == user_id,
                or_(CNCDraftingSession.status != "completed", CNCDraftingSession.status.is_(None)),
            )
        )
    ).all()
    timer_entries.extend(
        [f"CNC (FAB #{fab_id}, status: {status_value})" for fab_id, status_value in cnc_rows]
    )

    final_programming_rows = (
        await db.execute(
            select(FinalProgrammingSession.fab_id, FinalProgrammingSession.status)
            .where(
                FinalProgrammingSession.user_id == user_id,
                or_(FinalProgrammingSession.status != "completed", FinalProgrammingSession.status.is_(None)),
            )
        )
    ).all()
    timer_entries.extend(
        [
            f"Final Programming (FAB #{fab_id}, status: {status_value})"
            for fab_id, status_value in final_programming_rows
        ]
    )

    slab_smith_rows = (
        await db.execute(
            select(SlabSmithSession.fab_id, SlabSmithSession.status)
            .where(
                SlabSmithSession.user_id == user_id,
                or_(SlabSmithSession.status != "completed", SlabSmithSession.status.is_(None)),
            )
        )
    ).all()
    timer_entries.extend(
        [f"SlabSmith (FAB #{fab_id}, status: {status_value})" for fab_id, status_value in slab_smith_rows]
    )

    operator_rows = (
        await db.execute(
            select(OperatorJobTimerSession.job_id, OperatorJobTimerSession.fab_id, OperatorJobTimerSession.status)
            .where(
                OperatorJobTimerSession.operator_id == user_id,
                or_(OperatorJobTimerSession.status != "completed", OperatorJobTimerSession.status.is_(None)),
            )
        )
    ).all()
    timer_entries.extend(
        [
            f"Operator Job Timer (job #{job_id}, FAB #{fab_id}, status: {status_value})"
            for job_id, fab_id, status_value in operator_rows
        ]
    )

    shop_plan_rows = (
        await db.execute(
            select(ShopCutPlanTimerSession.shop_cut_plan_id, ShopCutPlanTimerSession.status)
            .where(
                ShopCutPlanTimerSession.operator_id == user_id,
                or_(ShopCutPlanTimerSession.status != "completed", ShopCutPlanTimerSession.status.is_(None)),
            )
        )
    ).all()
    timer_entries.extend(
        [f"Shop Cut Plan (plan #{plan_id}, status: {status_value})" for plan_id, status_value in shop_plan_rows]
    )

    installer_rows = (
        await db.execute(
            select(InstallerJobTimerSession.job_id, InstallerJobTimerSession.fab_id, InstallerJobTimerSession.status)
            .where(
                InstallerJobTimerSession.installer_id == user_id,
                or_(InstallerJobTimerSession.status != "completed", InstallerJobTimerSession.status.is_(None)),
            )
        )
    ).all()
    timer_entries.extend(
        [
            f"Installer Job Timer (job #{job_id}, FAB #{fab_id}, status: {status_value})"
            for job_id, fab_id, status_value in installer_rows
        ]
    )

    templater_rows = (
        await db.execute(
            select(TemplaterJobTimerSession.job_id, TemplaterJobTimerSession.fab_id, TemplaterJobTimerSession.status)
            .where(
                TemplaterJobTimerSession.templater_id == user_id,
                or_(TemplaterJobTimerSession.status != "completed", TemplaterJobTimerSession.status.is_(None)),
            )
        )
    ).all()
    timer_entries.extend(
        [
            f"Templater Job Timer (job #{job_id}, FAB #{fab_id}, status: {status_value})"
            for job_id, fab_id, status_value in templater_rows
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
