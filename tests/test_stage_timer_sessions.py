from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine

from src.app.routers import fabs


@pytest.fixture
def db():
    """Minimal session/user tables; the loader only reads these columns."""
    metadata = MetaData()
    users = Table(
        "users", metadata, Column("id", Integer, primary_key=True),
        Column("first_name", String), Column("last_name", String), Column("username", String),
    )
    cnc = Table("cnc_drafting_sessions", metadata, Column("id", Integer, primary_key=True),
                Column("fab_id", Integer), Column("drafter_id", Integer), Column("status", String))
    slabsmith = Table("slab_smith_sessions", metadata, Column("id", Integer, primary_key=True),
                      Column("fab_id", Integer), Column("user_id", Integer), Column("status", String))
    final_programming = Table("final_programming_sessions", metadata, Column("id", Integer, primary_key=True),
                              Column("fab_id", Integer), Column("user_id", Integer), Column("status", String))
    engine = create_engine("sqlite://")
    metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(users.insert(), [
            {"id": 1, "first_name": "Jane", "last_name": "Doe", "username": "jdoe"},
            {"id": 2, "first_name": None, "last_name": None, "username": "shop.tablet"},
        ])
        conn.execute(cnc.insert(), [
            {"id": 1, "fab_id": 10, "drafter_id": 1, "status": "completed"},
            {"id": 2, "fab_id": 10, "drafter_id": 1, "status": "drafting"},   # latest for FAB 10
            {"id": 3, "fab_id": 11, "drafter_id": 2, "status": "on_hold"},
        ])
        conn.execute(slabsmith.insert(), [{"id": 1, "fab_id": 10, "user_id": 1, "status": "paused"}])
        conn.execute(final_programming.insert(), [
            {"id": 5, "fab_id": 12, "user_id": 2, "status": "active"},
            {"id": 4, "fab_id": 12, "user_id": 1, "status": "completed"},
        ])
        yield SimpleNamespace(execute=AsyncMock(side_effect=conn.execute))
    engine.dispose()


@pytest.mark.asyncio
async def test_latest_session_per_fab_for_each_stage(db):
    sessions = await fabs._batch_load_stage_timer_sessions(db, [10, 11, 12, 13])

    assert sessions["cnc_session"] == {
        10: {"id": 2, "status": "drafting", "user_id": 1, "user_name": "Jane Doe"},
        11: {"id": 3, "status": "on_hold", "user_id": 2, "user_name": "shop.tablet"},
    }
    assert sessions["slabsmith_session"] == {10: {"id": 1, "status": "paused", "user_id": 1, "user_name": "Jane Doe"}}
    assert sessions["final_programming_session"] == {12: {"id": 5, "status": "active", "user_id": 2, "user_name": "shop.tablet"}}
    assert db.execute.await_count == 3


@pytest.mark.asyncio
async def test_no_fabs_skips_queries(db):
    sessions = await fabs._batch_load_stage_timer_sessions(db, [])
    assert sessions == {"cnc_session": {}, "slabsmith_session": {}, "final_programming_session": {}}
    db.execute.assert_not_awaited()


def test_every_fab_gets_each_session_key():
    fab_dicts = [{"id": 10}, {"id": 13}]
    fabs._attach_stage_timer_sessions(fab_dicts, {"cnc_session": {10: {"status": "drafting"}}})
    assert fab_dicts == [
        {"id": 10, "cnc_session": {"status": "drafting"}, "slabsmith_session": None, "final_programming_session": None},
        {"id": 13, "cnc_session": None, "slabsmith_session": None, "final_programming_session": None},
    ]
