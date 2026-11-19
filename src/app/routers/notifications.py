from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import get_db
from src.app.database.notification import Notification
from src.app.database.user import User
from src.app.middleware.jwt_auth import get_current_user
from src.app.utils.helpers import app_now, error_response, success_response

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _serialize(notification: Notification) -> dict:
    return {
        "id": notification.id,
        "event": notification.event,
        "title": notification.title,
        "message": notification.message,
        "fab_id": notification.fab_id,
        "job_id": notification.job_id,
        "is_read": notification.is_read,
        "read_at": notification.read_at.isoformat() if notification.read_at else None,
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
    }


@router.get("")
async def list_notifications(
    status: Literal["unread", "all"] = Query("unread", description="'unread' for the tray, 'all' for history"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The current user's notifications, newest first."""
    query = select(Notification).where(Notification.user_id == current_user.id)
    if status == "unread":
        query = query.where(Notification.is_read.is_(False))
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    rows = (
        await db.execute(query.order_by(Notification.created_at.desc(), Notification.id.desc()).offset(skip).limit(limit))
    ).scalars().all()
    return success_response({"items": [_serialize(n) for n in rows], "total": total}, "Notifications retrieved")


@router.get("/unread-count")
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = (
        await db.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        )
    ).scalar_one()
    return success_response({"count": count}, "Unread count retrieved")


@router.patch("/{notification_id}/read")
async def mark_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = await db.get(Notification, notification_id)
    if not notification or notification.user_id != current_user.id:
        raise error_response("Notification not found", 404)
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = app_now()
        await db.commit()
    return success_response(_serialize(notification), "Notification marked as read")


@router.post("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Clears the tray. Rows are kept, so they still appear in history."""
    result = await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .values(is_read=True, read_at=app_now())
    )
    await db.commit()
    return success_response({"updated": result.rowcount or 0}, "All notifications marked as read")
