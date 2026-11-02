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
from src.app.interface.generated_schemas import Drafting
from src.app.middleware.jwt_auth import get_current_user
from src.app.routers import completed_work_report

TABLES = [User, Account, BusinessJob, StoneType, StoneColor, Fab, Drafting]


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
            ins(User, [{"id": 1, "first_name": "Dana", "last_name": "Cad", "email": "d@x", "username": "d", "password": "x"},
                       {"id": 2, "first_name": "Eli", "last_name": "Cad", "email": "e@x", "username": "e", "password": "x"}])
            ins(Account, [{"id": 1, "name": "Casa Metta Design"}])
            ins(BusinessJob, [{"id": 1, "name": "2229 Thurman Roberts", "job_number": "21110", "account_id": 1}])
            ins(StoneType, [{"id": 1, "name": "Quartz", "status_id": 1, "created_by": 1}])
            ins(StoneColor, [{"id": 1, "name": "Celestial Sky", "status_id": 1, "created_by": 1}])
            ins(Fab, [{"id": f, "job_id": 1, "fab_type": "STANDARD", "sales_person_id": 1, "stone_type_id": 1,
                       "stone_color_id": 1, "stone_thickness_id": 1, "edge_id": 1, "total_sqft": sq, "input_area": "Kitchen"}
                      for f, sq in [(15001, 40.0), (15002, 25.5), (15003, 10.0)]])
            ins(Drafting, [
                {"id": 1, "fab_id": 15001, "drafter_id": 1, "status_id": 3, "is_completed": True, "drafter_end_date": datetime(2026, 10, 28, 9)},
                {"id": 2, "fab_id": 15002, "drafter_id": 2, "status_id": 3, "is_completed": True, "drafter_end_date": datetime(2026, 11, 1, 14)},
                {"id": 3, "fab_id": 15003, "drafter_id": 1, "status_id": 1, "is_completed": False, "drafter_end_date": None},
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


def test_cad_report_lists_completed_drafting_newest_first(client):
    data = client.get("/reports/completed-work", params={"department": "cad"}).json()["data"]
    assert data["person_label"] == "Drafter"
    assert data["total"] == 2 and data["total_sqft"] == 65.5
    first = data["items"][0]
    assert (first["fab_id"], first["employee_name"], first["job_number"], first["stone_type"], first["stone_color"]) == (
        15002, "Eli Cad", "21110", "Quartz", "Celestial Sky")
    assert [i["fab_id"] for i in data["items"]] == [15002, 15001]


def test_filters_by_date_range_drafter_and_search(client):
    get = lambda **p: client.get("/reports/completed-work", params={"department": "cad", **p}).json()["data"]
    assert [i["fab_id"] for i in get(start_date="2026-10-30")["items"]] == [15002]
    assert [i["fab_id"] for i in get(end_date="2026-10-28")["items"]] == [15001]
    assert [i["fab_id"] for i in get(employee_id=1)["items"]] == [15001]
    assert get(search="15001")["total"] == 1
    assert get(search="casa metta", search_type="account_name")["total"] == 2
    assert get(search="nope", search_type="job_name")["total"] == 0
