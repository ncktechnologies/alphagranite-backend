import uuid
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

import src.app.database.model_registry  # noqa: F401
from src.app.database import get_db
from src.app.database.account import Account
from src.app.database.business_job import BusinessJob
from src.app.database.fab import Fab
from src.app.database.stone_color import StoneColor
from src.app.database.stone_type import StoneType
from src.app.database.user import User
from src.app.interface.generated_schemas import (
    Drafting, DraftingSession, FinalProgramming, FinalProgrammingSession, Revision,
)
from src.app.middleware.jwt_auth import get_current_user
from src.app.routers import completed_work_report

TABLES = [User, Account, BusinessJob, StoneType, StoneColor, Fab, Drafting, DraftingSession,
          Revision, FinalProgramming, FinalProgrammingSession]


def _filled(model, row):
    """Give required columns with no default a placeholder so fixtures stay focused."""
    out = dict(row)
    for col in model.__table__.columns:
        if col.name in out or col.nullable or col.default is not None or col.server_default is not None or col.primary_key:
            continue
        impl = getattr(col.type, "impl", col.type)  # unwrap TypeDecorators (tz-aware timestamps)
        try:
            py = impl.python_type
        except NotImplementedError:
            py = str
        fillers = {datetime: datetime(2026, 1, 1), int: 0, float: 0.0, bool: False, uuid.UUID: uuid.uuid4()}
        out[col.name] = fillers.get(py, "")
    return out


@compiles(JSONB, "sqlite")
def _jsonb_on_sqlite(type_, compiler, **kw):
    return "JSON"


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync: [m.__table__.create(sync) for m in TABLES])
        def seed(sync):
            ins = lambda m, rows: sync.execute(m.__table__.insert(), [_filled(m, r) for r in rows])
            ins(User, [
                {"id": 1, "first_name": "Dana", "last_name": "Cad", "email": "d@x", "username": "d", "password": "x", "created_at": datetime(2026, 6, 1)},
                {"id": 2, "first_name": "Eli", "last_name": "Cad", "email": "e@x", "username": "e", "password": "x", "created_at": datetime(2026, 6, 1)},
                # Joined after go-live; picked up revisions on FABs drafted in Caspio.
                {"id": 3, "first_name": "Robert ", "last_name": "Late", "email": "r@x", "username": "r", "password": "x", "created_at": datetime(2026, 10, 16)},
                {"id": 9, "first_name": "Migration", "last_name": "Bot", "email": "migration@localhost", "username": "migration_bot", "password": "x", "created_at": datetime(2026, 10, 16)},
            ])
            ins(Account, [{"id": 1, "name": "Casa Metta Design"}])
            ins(BusinessJob, [{"id": 1, "name": "2229 Thurman Roberts", "job_number": "21110", "account_id": 1}])
            ins(StoneType, [{"id": 1, "name": "Quartz", "status_id": 1, "created_by": 1}])
            ins(StoneColor, [{"id": 1, "name": "Celestial Sky", "status_id": 1, "created_by": 1}])
            ins(Fab, [{"id": f, "job_id": 1, "fab_type": "STANDARD", "sales_person_id": 1, "stone_type_id": 1,
                       "stone_color_id": 1, "stone_thickness_id": 1, "edge_id": 1, "total_sqft": sq, "input_area": "Kitchen",
                       "final_programming_complete": False, "final_programming_completed_date": None, "drafter_id": None,
                       **extra}
                      for f, sq, extra in [
                          (15001, 40.0, {}),
                          (15002, 25.5, {}),
                          (15003, 10.0, {}),
                          # Caspio-era draft, final programming done in Caspio (migrated row below)
                          (15004, 12.0, {"final_programming_complete": True,
                                         "final_programming_completed_date": datetime(2026, 10, 2, 9)}),
                          # Final programming done in Odyssey: stamped on the FAB, timed by Dana
                          (15005, 8.0, {"final_programming_complete": True, "drafter_id": 2,
                                        "final_programming_completed_date": datetime(2026, 11, 5, 15)}),
                      ]])
            ins(Drafting, [
                {"id": 1, "fab_id": 15001, "drafter_id": 1, "status_id": 3, "is_completed": True, "drafter_end_date": datetime(2026, 10, 28, 9)},
                # Drafted by Eli, then reassigned to Robert for a revision
                {"id": 2, "fab_id": 15002, "drafter_id": 3, "status_id": 3, "is_completed": True, "drafter_end_date": datetime(2026, 11, 1, 14)},
                {"id": 3, "fab_id": 15003, "drafter_id": 1, "status_id": 1, "is_completed": False, "drafter_end_date": None},
                # Migrated Caspio draft later reassigned to Robert, who didn't work here yet on 10/01
                {"id": 4, "fab_id": 15004, "drafter_id": 3, "status_id": 1, "is_completed": True, "drafter_end_date": datetime(2026, 10, 1, 4)},
            ])
            ins(DraftingSession, [
                {"id": 1, "fab_id": 15002, "drafter_id": 2, "status": "completed",
                 "session_start_time": datetime(2026, 11, 1, 9), "session_end_time": datetime(2026, 11, 1, 14)},
                # Robert's revision session on the same FAB, after the draft was done
                {"id": 2, "fab_id": 15002, "drafter_id": 3, "status": "completed",
                 "session_start_time": datetime(2026, 11, 10, 9), "session_end_time": datetime(2026, 11, 10, 11)},
            ])
            ins(Revision, [
                {"id": 1, "fab_id": 15002, "revision_type": "cad", "requested_by": 1, "is_completed": True, "status_id": 1,
                 "created_at": datetime(2026, 11, 9), "actual_end_date": datetime(2026, 11, 10, 11), "updated_by": 3},
                {"id": 2, "fab_id": 15001, "revision_type": "client", "requested_by": 1, "is_completed": False, "status_id": 1,
                 "created_at": datetime(2026, 11, 12), "actual_end_date": None, "updated_by": None},
                {"id": 3, "fab_id": 15004, "revision_type": "SHOP", "requested_by": 9, "is_completed": True, "status_id": 1,
                 "created_at": datetime(2026, 9, 1), "actual_end_date": datetime(2026, 9, 3), "updated_by": 9},
            ])
            ins(FinalProgramming, [
                {"id": 1, "fab_id": 15004, "drafter_id": 9, "is_completed": True, "status_id": 1,
                 "drafter_end_date": datetime(2026, 10, 2, 9)},
            ])
            ins(FinalProgrammingSession, [
                {"id": 1, "fab_id": 15005, "user_id": 1, "status": "completed",
                 "session_start_time": datetime(2026, 11, 5, 13), "session_end_time": datetime(2026, 11, 5, 14, 55)},
            ])
        await conn.run_sync(seed)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def db_override():
        async with factory() as db:
            yield db

    app = FastAPI()
    app.include_router(completed_work_report.router)
    app.dependency_overrides[get_db] = db_override
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1)
    # SQLite compares naive timestamps; production uses the app timezone.
    with patch.object(completed_work_report, "to_app_tz", lambda value: value):
        yield TestClient(app)
    await engine.dispose()


def _report(client, department="cad", **params):
    return client.get("/reports/completed-work", params={"department": department, **params}).json()["data"]


def test_cad_report_lists_completed_drafting_newest_first(client):
    data = _report(client)
    assert data["person_label"] == "Drafter"
    assert data["total"] == 3 and data["total_sqft"] == 77.5
    first = data["items"][0]
    assert (first["fab_id"], first["employee_name"], first["job_number"], first["stone_type"], first["stone_color"]) == (
        15002, "Eli Cad", "21110", "Quartz", "Celestial Sky")
    assert [i["fab_id"] for i in data["items"]] == [15002, 15001, 15004]


def test_reassigning_a_drafted_fab_does_not_re_credit_the_drafting(client):
    by_fab = {i["fab_id"]: i for i in _report(client)["items"]}
    # Eli ran the drafting session; Robert was only reassigned for the revision afterwards.
    assert (by_fab[15002]["employee_id"], by_fab[15002]["employee_name"]) == (2, "Eli Cad")
    # Caspio draft from 10/01 reassigned to someone who joined 10/16: legacy, not Robert.
    assert by_fab[15004]["is_legacy"] is True
    assert (by_fab[15004]["employee_id"], by_fab[15004]["employee_name"]) == (None, "Legacy (Caspio)")


def test_filters_by_date_range_drafter_and_search(client):
    get = lambda **p: _report(client, **p)
    assert [i["fab_id"] for i in get(start_date="2026-10-30")["items"]] == [15002]
    assert [i["fab_id"] for i in get(end_date="2026-10-28")["items"]] == [15001, 15004]
    assert [i["fab_id"] for i in get(employee_id=1)["items"]] == [15001]
    assert [i["fab_id"] for i in get(employee_id=2)["items"]] == [15002]
    assert get(employee_id=3)["total"] == 0  # Robert drafted none of these
    assert get(search="15001")["total"] == 1
    assert get(search="casa metta", search_type="account_name")["total"] == 3
    assert get(search="nope", search_type="job_name")["total"] == 0


def test_revisions_credit_whoever_ran_the_revision_session(client):
    data = _report(client, "revisions")
    assert (data["department_label"], data["person_label"]) == ("CAD - Revisions", "Revisor")
    assert [(i["fab_id"], i["employee_name"]) for i in data["items"]] == [
        (15002, "Robert Late"), (15004, "Legacy (Caspio)")]
    assert [i["fab_id"] for i in _report(client, "revisions", employee_id=3)["items"]] == [15002]


def test_final_programming_reads_completions_stamped_on_the_fab(client):
    data = _report(client, "final_programming")
    assert [(i["fab_id"], i["completed_on"][:10], i["employee_name"]) for i in data["items"]] == [
        (15005, "2026-11-05", "Dana Cad"),  # session user, not the FAB's drafter
        (15004, "2026-10-02", "Legacy (Caspio)"),
    ]
    assert _report(client, "final_programming", start_date="2026-11-01")["total"] == 1


def test_departments_include_revisions():
    from src.app.routers.completed_work_report import DEPARTMENTS
    assert list(DEPARTMENTS) == ["cad", "revisions", "cnc", "slabsmith", "final_programming"]
