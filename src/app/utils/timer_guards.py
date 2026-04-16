"""Cross-endpoint active-timer guard.

Checks all DB-backed timer session tables to ensure a user does not already
have a running timer session before starting or resuming another.

Usage in route handlers (skip for super admins):

    if not getattr(current_user, "is_super_admin", False):
        await assert_no_active_timer_session(db, user_id)
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.database.business_job import BusinessJob
from src.app.database.cnc import CNCDraftingSession
from src.app.database.drafting import DraftingSession
from src.app.database.fab import Fab
from src.app.database.installer_job_timer_session import InstallerJobTimerSession
from src.app.database.operator_job_timer_session import OperatorJobTimerSession
from src.app.database.shop_cut_plan_timer_session import ShopCutPlanTimerSession
from src.app.database.templater_job_timer_session import TemplaterJobTimerSession


async def assert_no_active_timer_session(db: AsyncSession, user_id: int) -> None:
    """Raise HTTP 409 if *user_id* already has a running timer in any DB-backed
    session table.

    Does NOT apply super-admin logic — callers are responsible for skipping
    this call when ``current_user.is_super_admin`` is True.
    """

    # ── DraftingSession ──────────────────────────────────────────────────────
    row = (
        await db.execute(
            select(DraftingSession, BusinessJob)
            .join(Fab, Fab.id == DraftingSession.fab_id)
            .join(BusinessJob, BusinessJob.id == Fab.job_id)
            .where(
                DraftingSession.drafter_id == user_id,
                DraftingSession.status == "drafting",
            )
            .limit(1)
        )
    ).first()
    if row:
        sess, job = row
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A drafting session for Job #{job.job_number} "
                f"(FAB #{sess.fab_id}) is already running. "
                "Pause it before starting another timer."
            ),
        )

    # ── CNCDraftingSession ───────────────────────────────────────────────────
    row = (
        await db.execute(
            select(CNCDraftingSession, BusinessJob)
            .join(Fab, Fab.id == CNCDraftingSession.fab_id)
            .join(BusinessJob, BusinessJob.id == Fab.job_id)
            .where(
                CNCDraftingSession.drafter_id == user_id,
                CNCDraftingSession.status == "drafting",
            )
            .limit(1)
        )
    ).first()
    if row:
        sess, job = row
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A CNC session for Job #{job.job_number} "
                f"(FAB #{sess.fab_id}) is already running. "
                "Pause it before starting another timer."
            ),
        )

    # ── OperatorJobTimerSession ──────────────────────────────────────────────
    row = (
        await db.execute(
            select(OperatorJobTimerSession, BusinessJob)
            .join(BusinessJob, BusinessJob.id == OperatorJobTimerSession.job_id)
            .where(
                OperatorJobTimerSession.operator_id == user_id,
                OperatorJobTimerSession.status == "running",
            )
            .limit(1)
        )
    ).first()
    if row:
        sess, job = row
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A job timer for Job #{job.job_number} "
                f"(FAB #{sess.fab_id}) is already running. "
                "Pause it before starting another timer."
            ),
        )

    # ── ShopCutPlanTimerSession ──────────────────────────────────────────────
    sess = (
        await db.execute(
            select(ShopCutPlanTimerSession)
            .where(
                ShopCutPlanTimerSession.operator_id == user_id,
                ShopCutPlanTimerSession.status == "running",
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if sess:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A shop cut plan timer (Plan #{sess.shop_cut_plan_id}) "
                "is already running. "
                "Pause it before starting another timer."
            ),
        )

    # ── InstallerJobTimerSession ─────────────────────────────────────────────
    row = (
        await db.execute(
            select(InstallerJobTimerSession, BusinessJob)
            .join(BusinessJob, BusinessJob.id == InstallerJobTimerSession.job_id)
            .where(
                InstallerJobTimerSession.installer_id == user_id,
                InstallerJobTimerSession.status == "running",
            )
            .limit(1)
        )
    ).first()
    if row:
        sess, job = row
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"An installer timer for Job #{job.job_number} "
                f"(FAB #{sess.fab_id}) is already running. "
                "Pause it before starting another timer."
            ),
        )

    # ── TemplaterJobTimerSession ─────────────────────────────────────────────
    row = (
        await db.execute(
            select(TemplaterJobTimerSession, BusinessJob)
            .join(BusinessJob, BusinessJob.id == TemplaterJobTimerSession.job_id)
            .where(
                TemplaterJobTimerSession.templater_id == user_id,
                TemplaterJobTimerSession.status == "running",
            )
            .limit(1)
        )
    ).first()
    if row:
        sess, job = row
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A templater timer for Job #{job.job_number} "
                f"(FAB #{sess.fab_id}) is already running. "
                "Pause it before starting another timer."
            ),
        )
