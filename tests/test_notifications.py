from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.app.database import get_db
from src.app.database.notification import Notification
from src.app.middleware.jwt_auth import get_current_user
from src.app.routers import notifications as notifications_router
from src.app.service import notifications


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Notification.__table__.create)
    yield async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await engine.dispose()


class FakeLookups:
    """Stands in for fab/job lookups; notifications are written to the real session."""

    def __init__(self, session):
        self.session = session
        self.fab = SimpleNamespace(id=15234, job_id=7, sales_person_id=21, input_area="Kitchen", stone_color_id=None)
        self.job = SimpleNamespace(name="2229 Thurman Roberts", account_id=None, job_number="21110")

    async def get(self, model, key):
        return {"Fab": self.fab, "BusinessJob": self.job}.get(model.__name__)

    def __getattr__(self, name):
        return getattr(self.session, name)


def factory_with_lookups(session_factory):
    class _Ctx:
        async def __aenter__(self):
            self.session = session_factory()
            return FakeLookups(await self.session.__aenter__())

        async def __aexit__(self, *exc):
            await self.session.__aexit__(*exc)

    return _Ctx


async def stored(session_factory):
    async with session_factory() as db:
        return (await db.execute(select(Notification).order_by(Notification.user_id))).scalars().all()


@pytest.mark.asyncio
async def test_draft_submitted_goes_to_the_fabs_sales_person(session_factory):
    count = await notifications.notify_fab_event(15234, "draft_submitted", actor_id=5, session_factory=factory_with_lookups(session_factory))

    rows = await stored(session_factory)
    assert count == 1
    assert [(r.user_id, r.title, r.message, r.fab_id) for r in rows] == [
        (21, "Draft Submitted", "2229 Thurman Roberts #15234 Draft Submitted", 15234)
    ]


@pytest.mark.asyncio
async def test_shop_revision_request_goes_to_all_drafters_except_the_requester(session_factory):
    with patch.object(notifications, "_user_ids_with_roles", AsyncMock(return_value={3, 4, 5})) as roles:
        await notifications.notify_fab_event(15234, "shop_revision_requested", actor_id=4, session_factory=factory_with_lookups(session_factory))

    assert roles.await_args.args[1] == ["cad", "drafter"]
    assert [(r.user_id, r.message) for r in await stored(session_factory)] == [
        (3, "2229 Thurman Roberts #15234 Shop Revision Requested"),
        (5, "2229 Thurman Roberts #15234 Shop Revision Requested"),
    ]


@pytest.mark.asyncio
async def test_failures_never_reach_the_caller():
    def broken_factory():
        raise RuntimeError("database down")

    assert await notifications.notify_fab_event(1, "draft_submitted", 1, session_factory=broken_factory) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "old, new",
    [(None, datetime(2026, 11, 4)), (datetime(2026, 11, 4, 9), datetime(2026, 11, 4, 15)), ("2026-11-04", "2026-11-04")],
)
async def test_date_email_only_when_an_established_date_changes(old, new):
    with patch.object(notifications, "send_email") as send:
        assert await notifications.email_est_completion_date_change(1, old, new) is False
    send.assert_not_called()


@pytest.mark.asyncio
async def test_date_change_email_lists_job_and_both_dates(session_factory):
    with patch.object(notifications, "send_email") as send:
        sent = await notifications.email_est_completion_date_change(
            15234, datetime(2026, 11, 4), "2026-11-09", session_factory=factory_with_lookups(session_factory)
        )
    assert sent is True
    recipients, subject, body, _ = send.call_args.args
    assert recipients == notifications.EST_DATE_CHANGE_RECIPIENTS
    assert subject == "Est. Completion Date Changed - 2229 Thurman Roberts #15234"
    for text in ("2229 Thurman Roberts", "21110", "15234", "Kitchen", "11/04/2026", "11/09/2026"):
        assert text in body


@pytest.mark.asyncio
async def test_mark_all_read_empties_tray_but_keeps_history(session_factory):
    async with session_factory() as db:
        for user_id, title in [(1, "A"), (1, "B"), (2, "Other user")]:
            db.add(Notification(user_id=user_id, event="draft_submitted", title=title, message=title))
        await db.commit()

    app = FastAPI()
    app.include_router(notifications_router.router)

    async def db_override():
        async with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = db_override
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1)
    client = TestClient(app)

    assert client.get("/notifications/unread-count").json()["data"]["count"] == 2
    assert client.post("/notifications/read-all").json()["data"]["updated"] == 2
    assert client.get("/notifications").json()["data"]["items"] == []
    history = client.get("/notifications", params={"status": "all"}).json()["data"]
    assert history["total"] == 2 and all(item["is_read"] for item in history["items"])
    # Another user's notifications are untouched.
    async with session_factory() as db:
        other = (await db.execute(select(Notification).where(Notification.user_id == 2))).scalar_one()
        assert other.is_read is False
