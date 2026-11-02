"""
In-app (bell) notifications and the estimated-completion-date email, per the
front office's alerts spec.

Every public function here is best-effort: it runs after the triggering action
has committed, uses its own database session, and never raises, so an alert
problem can't undo, fail, or disturb the request's work.
"""
import asyncio
import logging
import os
from datetime import date, datetime
from functools import partial
from typing import Iterable, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.account import Account
from src.app.database.business_job import BusinessJob
from src.app.database.fab import Fab
from src.app.database.notification import Notification
from src.app.database.role import Role
from src.app.database.stone_color import StoneColor
from src.app.database.user import User
from src.app.database.user_role import UserRole
from src.app.service.background import send_email
from src.app.utils.config import SessionLocal
from src.app.utils.helpers import app_now

logger = logging.getLogger("notifications")

SALES_PERSON = "sales_person"
DRAFTERS = "drafters"
SHOP_PLANNERS = "shop_planners"

# event -> (description shown after "Job Name #FabID", who receives it)
FAB_EVENTS = {
    "draft_submitted": ("Draft Submitted", SALES_PERSON),
    "sales_revision_completed": ("Sales Revision Completed", SALES_PERSON),
    "slabsmith_completed": ("SlabSmith Completed", SALES_PERSON),
    "shop_revision_requested": ("Shop Revision Requested", DRAFTERS),
    "shop_revision_completed": ("Shop Revision Completed", SHOP_PLANNERS),
    "sales_revision_requested": ("Sales Revision Requested", DRAFTERS),
}

# Role names differ per environment, so they're configurable (comma-separated, case-insensitive).
ROLE_NAMES = {
    DRAFTERS: ("NOTIFY_DRAFTER_ROLES", "CAD,Drafter"),
    SHOP_PLANNERS: ("NOTIFY_SHOP_PLANNER_ROLES", "Shop Planner,Shop Planning,Planner"),
}

EST_DATE_CHANGE_RECIPIENTS = (
    "templates@alphagraniteaustin.com,install@alphagraniteaustin.com,keziah@alphagraniteaustin.com"
)


def _role_names(audience: str) -> list[str]:
    env_name, default = ROLE_NAMES[audience]
    return [name.strip().lower() for name in os.getenv(env_name, default).split(",") if name.strip()]


async def _user_ids_with_roles(db: AsyncSession, role_names: list[str]) -> set[int]:
    """Active users whose primary role or any assigned role matches one of the names."""
    if not role_names:
        return set()
    role_ids = select(Role.id).where(func.lower(func.trim(Role.name)).in_(role_names))
    assigned = select(UserRole.user_id).where(UserRole.role_id.in_(role_ids))
    result = await db.execute(
        select(User.id).where(
            or_(User.role_id.in_(role_ids), User.id.in_(assigned)),
            or_(User.status.is_(None), User.status == 1),
        )
    )
    return {row[0] for row in result.all()}


async def _recipients(db: AsyncSession, audience: str, fab: Fab) -> set[int]:
    if audience == SALES_PERSON:
        return {fab.sales_person_id} if fab.sales_person_id else set()
    return await _user_ids_with_roles(db, _role_names(audience))


async def create_notifications(
    db: AsyncSession,
    user_ids: Iterable[int],
    *,
    event: str,
    title: str,
    message: str,
    fab_id: Optional[int] = None,
    job_id: Optional[int] = None,
    created_by: Optional[int] = None,
) -> int:
    now = app_now()
    rows = [
        Notification(
            user_id=user_id, event=event, title=title, message=message,
            fab_id=fab_id, job_id=job_id, created_by=created_by, created_at=now,
        )
        for user_id in sorted(set(user_ids))
    ]
    db.add_all(rows)
    await db.commit()
    return len(rows)


async def notify_fab_event(fab_id: int, event: str, actor_id: Optional[int] = None, session_factory=SessionLocal) -> int:
    """Notify the event's audience about a FAB, e.g. "2229 Thurman Roberts #15234 Draft Submitted".
    The person who caused the event isn't notified about their own action."""
    try:
        async with session_factory() as db:
            return await _notify_fab_event(db, fab_id, event, actor_id)
    except Exception:
        logger.exception("Failed to create %s notifications for FAB %s", event, fab_id)
        return 0


async def _notify_fab_event(db: AsyncSession, fab_id: int, event: str, actor_id: Optional[int]) -> int:
    description, audience = FAB_EVENTS[event]
    fab = await db.get(Fab, fab_id)
    if fab is None:
        return 0
    job = await db.get(BusinessJob, fab.job_id) if fab.job_id else None
    recipients = await _recipients(db, audience, fab)
    recipients.discard(actor_id)
    if not recipients:
        return 0
    job_name = job.name if job else "Job"
    return await create_notifications(
        db,
        recipients,
        event=event,
        title=description,
        message=f"{job_name} #{fab.id} {description}",
        fab_id=fab.id,
        job_id=fab.job_id,
        created_by=actor_id,
    )


def _as_date(value) -> Optional[date]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()


def _format_date(value: Optional[date]) -> str:
    return value.strftime("%m/%d/%Y") if value else "—"


_background_tasks: set[asyncio.Task] = set()


def schedule_est_completion_date_email(fab_id: int, old_value, new_value) -> None:
    """Send the date-change email without making the save wait on SMTP."""
    task = asyncio.create_task(email_est_completion_date_change(fab_id, old_value, new_value))
    _background_tasks.add(task)  # keep a reference until it finishes
    task.add_done_callback(_background_tasks.discard)


async def email_est_completion_date_change(fab_id: int, old_value, new_value, session_factory=SessionLocal) -> bool:
    """Email the front office when an already-set shop Est. Completion Date changes.
    Setting the date for the first time, or saving the same day again, sends nothing."""
    try:
        old_date, new_date = _as_date(old_value), _as_date(new_value)
        if old_date is None or new_date is None or old_date == new_date:
            return False
        async with session_factory() as db:
            return await _email_est_completion_date_change(db, fab_id, old_date, new_date)
    except Exception:
        logger.exception("Failed to email Est. Completion Date change for FAB %s", fab_id)
        return False


async def _email_est_completion_date_change(db: AsyncSession, fab_id: int, old_date: date, new_date: date) -> bool:
    fab = await db.get(Fab, fab_id)
    if fab is None:
        return False
    job = await db.get(BusinessJob, fab.job_id) if fab.job_id else None
    account = await db.get(Account, job.account_id) if job and job.account_id else None
    color = await db.get(StoneColor, fab.stone_color_id) if fab.stone_color_id else None

    rows = [
        ("Account Name", account.name if account else "—"),
        ("Job Name", job.name if job else "—"),
        ("Job Number", job.job_number if job else "—"),
        ("Fab ID", str(fab.id)),
        ("Area", fab.input_area or "—"),
        ("Color", color.name if color else "—"),
        ("Old Est. Completion Date", _format_date(old_date)),
        ("New Est. Completion Date", _format_date(new_date)),
    ]
    body = (
        "<p>The shop Estimated Completion Date has changed.</p><table cellpadding='4'>"
        + "".join(f"<tr><td><strong>{label}</strong></td><td>{value}</td></tr>" for label, value in rows)
        + "</table>"
    )
    recipients = os.getenv("EST_DATE_CHANGE_EMAIL_RECIPIENTS", EST_DATE_CHANGE_RECIPIENTS)
    subject = f"Est. Completion Date Changed - {job.name if job else 'Job'} #{fab.id}"
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, partial(send_email, recipients, subject, body, True))
    return True
