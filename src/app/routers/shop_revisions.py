from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.app.database import get_db
from src.app.database.account import Account
from src.app.database.business_job import BusinessJob
from src.app.database.fab import Fab
from src.app.database.user import User
from src.app.interface.generated_schemas import ShopRevision
from src.app.interface.business_schemas import (
    ShopRevisionCreate,
    ShopRevisionResponse,
    ShopRevisionUpdate,
)
from src.app.interface.response_wrappers import SuccessResponse
from src.app.middleware.jwt_auth import get_current_user
from src.app.service.background import send_notification
from src.app.utils.config import SUPPORT_EMAIL
from src.app.utils.helpers import error_response, success_response


router = APIRouter(
    prefix="/shop-revisions",
    tags=["Shop Revisions"],
)


def _serialize_shop_revision(revision: ShopRevision) -> dict:
    return {
        "id": revision.id,
        "fab_id": revision.fab_id,
        "revision_note": revision.revision_note,
        "requested_by": revision.requested_by,
        "assigned_to": revision.assigned_to,
        "revision_completed": revision.revision_completed,
        "completed_at": revision.completed_at.isoformat() if revision.completed_at else None,
        "created_at": revision.created_at.isoformat() if revision.created_at else None,
        "updated_at": revision.updated_at.isoformat() if revision.updated_at else None,
        "updated_by": revision.updated_by,
    }


def _serialize_shop_revision_row(
    revision: ShopRevision,
    fab: Fab,
    job: Optional[BusinessJob],
    requester: Optional[User],
    assignee: Optional[User],
) -> dict:
    payload = _serialize_shop_revision(revision)
    payload["fab"] = {
        "id": fab.id,
        "job_id": fab.job_id,
        "job_number": job.job_number if job else None,
        "job_name": job.name if job else None,
        "fab_type": fab.fab_type,
        "current_stage": fab.current_stage,
        "status_id": fab.status_id,
        "has_pending_shop_revision": True,
    }
    payload["requested_by_name"] = (
        f"{requester.first_name} {requester.last_name}".strip() if requester else None
    )
    payload["assigned_to_name"] = (
        f"{assignee.first_name} {assignee.last_name}".strip() if assignee else None
    )
    return payload


@router.post("", response_model=SuccessResponse[ShopRevisionResponse], status_code=201)
async def create_shop_revision(
    revision_data: ShopRevisionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new shop revision request."""
    fab = (await db.execute(select(Fab).where(Fab.id == revision_data.fab_id))).scalar_one_or_none()
    if not fab:
        raise error_response("Fab not found", 404)

    if revision_data.requested_by is not None and revision_data.requested_by != current_user.id:
        raise error_response("requested_by must match the authenticated user", 403)

    assigned_to_user = None
    if revision_data.assigned_to is not None:
        assigned_to_user = (
            await db.execute(select(User).where(User.id == revision_data.assigned_to))
        ).scalar_one_or_none()
        if not assigned_to_user:
            raise error_response("Assigned user not found", 404)

    now = datetime.now()
    revision = ShopRevision(
        fab_id=revision_data.fab_id,
        revision_note=revision_data.revision_note,
        requested_by=current_user.id,
        assigned_to=revision_data.assigned_to,
        revision_completed=bool(revision_data.revision_completed),
        completed_at=now if revision_data.revision_completed else None,
        created_at=now,
        updated_at=now,
        updated_by=current_user.id,
    )

    db.add(revision)
    await db.commit()
    await db.refresh(revision)

    requester_name = f"{current_user.first_name} {current_user.last_name}".strip()
    assignee_name = (
        f"{assigned_to_user.first_name} {assigned_to_user.last_name}".strip()
        if assigned_to_user
        else "Unassigned"
    )
    background_tasks.add_task(
        send_notification,
        db,
        SUPPORT_EMAIL,
        f"Shop revision created for FAB #{fab.id}",
        f"""
        <html>
          <body>
            <p>A new shop revision has been created.</p>
            <ul>
              <li><strong>FAB ID:</strong> {fab.id}</li>
              <li><strong>Job ID:</strong> {fab.job_id}</li>
              <li><strong>Requested By:</strong> {requester_name}</li>
              <li><strong>Assigned To:</strong> {assignee_name}</li>
              <li><strong>Revision Note:</strong> {revision.revision_note}</li>
              <li><strong>Completed:</strong> {revision.revision_completed}</li>
              <li><strong>Created At:</strong> {now.isoformat()}</li>
            </ul>
          </body>
        </html>
        """,
        current_user.id,
    )

    return success_response(_serialize_shop_revision(revision), "Shop revision created successfully")


@router.get("", response_model=SuccessResponse[List[dict]])
async def get_shop_revisions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all pending shop revision rows."""
    _ = current_user

    RequesterUser = aliased(User)
    AssigneeUser = aliased(User)

    result = await db.execute(
        select(ShopRevision, Fab, BusinessJob, RequesterUser, AssigneeUser)
        .join(Fab, Fab.id == ShopRevision.fab_id)
        .join(BusinessJob, BusinessJob.id == Fab.job_id, isouter=True)
        .join(RequesterUser, RequesterUser.id == ShopRevision.requested_by, isouter=True)
        .join(AssigneeUser, AssigneeUser.id == ShopRevision.assigned_to, isouter=True)
        .where(ShopRevision.revision_completed.is_(False))
        .order_by(ShopRevision.created_at.desc(), ShopRevision.id.desc())
    )
    rows = result.all()

    # Re-query with distinct aliases to avoid column ambiguity in serialization.
    pending_rows = []
    for row in rows:
        revision = row[0]
        fab = row[1]
        job = row[2]
        requested_by = row[3]
        assigned_to = row[4]
        pending_rows.append(
            _serialize_shop_revision_row(revision, fab, job, requested_by, assigned_to)
        )

    return success_response(pending_rows, "Shop revisions retrieved successfully")


@router.get("/fab/{fab_id}", response_model=SuccessResponse[List[dict]])
async def get_shop_revisions_by_fab(
    fab_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all shop revisions for a FAB, pending and completed."""
    _ = current_user

    RequesterUser = aliased(User)
    AssigneeUser = aliased(User)

    result = await db.execute(
        select(ShopRevision, Fab, BusinessJob, RequesterUser, AssigneeUser)
        .join(Fab, Fab.id == ShopRevision.fab_id)
        .join(BusinessJob, BusinessJob.id == Fab.job_id, isouter=True)
        .join(RequesterUser, RequesterUser.id == ShopRevision.requested_by, isouter=True)
        .join(AssigneeUser, AssigneeUser.id == ShopRevision.assigned_to, isouter=True)
        .where(ShopRevision.fab_id == fab_id)
        .order_by(ShopRevision.created_at.desc(), ShopRevision.id.desc())
    )
    rows = result.all()

    if not rows:
        return success_response([], "No shop revisions found for this fab")

    data = []
    for row in rows:
        data.append(_serialize_shop_revision_row(row[0], row[1], row[2], row[3], row[4]))

    return success_response(data, "Shop revisions retrieved successfully")


@router.get("/fabs", response_model=SuccessResponse[List[dict]])
async def get_fabs_with_pending_shop_revisions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all FABs that still have at least one pending shop revision."""
    _ = current_user

    RequesterUser = aliased(User)
    AssigneeUser = aliased(User)

    counts_result = await db.execute(
        select(ShopRevision.fab_id, func.count(ShopRevision.id).label("revision_count"))
        .where(ShopRevision.revision_completed.is_(False))
        .group_by(ShopRevision.fab_id)
        .order_by(ShopRevision.fab_id.desc())
    )
    counts = {row[0]: int(row[1] or 0) for row in counts_result.all()}

    if not counts:
        return success_response([], "No FABs with pending shop revisions found")

    fab_ids = list(counts.keys())

    fab_rows = (
        await db.execute(
            select(Fab, BusinessJob, Account)
            .join(BusinessJob, BusinessJob.id == Fab.job_id, isouter=True)
            .join(Account, Account.id == BusinessJob.account_id, isouter=True)
            .where(Fab.id.in_(fab_ids))
            .order_by(Fab.id.desc())
        )
    ).all()

    latest_revision_rows = (
        await db.execute(
            select(ShopRevision, RequesterUser, AssigneeUser)
            .join(RequesterUser, RequesterUser.id == ShopRevision.requested_by, isouter=True)
            .join(AssigneeUser, AssigneeUser.id == ShopRevision.assigned_to, isouter=True)
            .where(
                ShopRevision.fab_id.in_(fab_ids),
                ShopRevision.revision_completed.is_(False),
            )
            .order_by(ShopRevision.fab_id, ShopRevision.created_at.desc(), ShopRevision.id.desc())
        )
    ).all()

    latest_revision_by_fab = {}
    for row in latest_revision_rows:
        revision = row[0]
        if revision.fab_id not in latest_revision_by_fab:
            latest_revision_by_fab[revision.fab_id] = {
                "id": revision.id,
                "revision_note": revision.revision_note,
                "requested_by": revision.requested_by,
                "assigned_to": revision.assigned_to,
                "revision_completed": revision.revision_completed,
                "completed_at": revision.completed_at.isoformat() if revision.completed_at else None,
                "created_at": revision.created_at.isoformat() if revision.created_at else None,
                "updated_at": revision.updated_at.isoformat() if revision.updated_at else None,
                "updated_by": revision.updated_by,
            }

    data = []
    for fab, job, account in fab_rows:
        data.append(
            {
                "fab_id": fab.id,
                "job_id": fab.job_id,
                "job_number": job.job_number if job else None,
                "job_name": job.name if job else None,
                "account_name": account.name if account else None,
                "fab_type": fab.fab_type,
                "current_stage": fab.current_stage,
                "status_id": fab.status_id,
                "pending_revision_count": counts.get(fab.id, 0),
                "has_pending_shop_revision": True,
                "latest_pending_revision": latest_revision_by_fab.get(fab.id),
            }
        )

    return success_response(data, "FABs with pending shop revisions retrieved successfully")


@router.patch("/{revision_id}/complete", response_model=SuccessResponse[ShopRevisionResponse])
async def complete_shop_revision(
    revision_id: int,
    revision_data: Optional[ShopRevisionUpdate] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a shop revision as completed."""
    result = await db.execute(select(ShopRevision).where(ShopRevision.id == revision_id))
    revision = result.scalar_one_or_none()
    if not revision:
        raise error_response("Shop revision not found", 404)

    now = datetime.now()
    if revision_data and revision_data.revision_note:
        revision.revision_note = revision_data.revision_note
    if revision_data and revision_data.assigned_to is not None:
        assigned_to_user = (
            await db.execute(select(User).where(User.id == revision_data.assigned_to))
        ).scalar_one_or_none()
        if not assigned_to_user:
            raise error_response("Assigned user not found", 404)
        revision.assigned_to = revision_data.assigned_to

    revision.revision_completed = True
    revision.completed_at = now
    revision.updated_at = now
    revision.updated_by = current_user.id

    db.add(revision)
    await db.commit()
    await db.refresh(revision)

    return success_response(_serialize_shop_revision(revision), "Shop revision completed successfully")