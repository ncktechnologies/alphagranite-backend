from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine

from src.app.interface.business_schemas import (
    CNCDraftingCreate,
    CNCDraftingUpdate,
    SlabSmithCreate,
    DraftingUpdate,
    FinalProgrammingUpdate,
    RevisionUpdate,
    SlabSmithUpdate,
)
from src.app.routers import cnc, drafting, final_programming, revisions, slabsmith_sales_ct
from src.app.utils import timer_guards
from src.app.utils.timer_guards import assert_no_running_timer_for_reassignment

JANE, BOB, NO_NAME = 1, 2, 3


@pytest.fixture
def db():
    """Minimal session/user tables; the guard only reads these columns."""
    metadata = MetaData()
    users = Table(
        "users", metadata, Column("id", Integer, primary_key=True),
        Column("first_name", String), Column("last_name", String), Column("username", String),
    )
    tables = {
        "drafting": Table("drafting_sessions", metadata, Column("id", Integer, primary_key=True),
                          Column("fab_id", Integer), Column("drafter_id", Integer), Column("status", String)),
        "cnc": Table("cnc_drafting_sessions", metadata, Column("id", Integer, primary_key=True),
                     Column("fab_id", Integer), Column("drafter_id", Integer), Column("status", String)),
        "final_programming": Table("final_programming_sessions", metadata, Column("id", Integer, primary_key=True),
                                   Column("fab_id", Integer), Column("user_id", Integer), Column("status", String)),
        "slabsmith": Table("slab_smith_sessions", metadata, Column("id", Integer, primary_key=True),
                           Column("fab_id", Integer), Column("user_id", Integer), Column("status", String)),
    }
    engine = create_engine("sqlite://")
    metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(users.insert(), [
            {"id": JANE, "first_name": "Jane", "last_name": "Doe", "username": "jdoe"},
            {"id": BOB, "first_name": "Bob", "last_name": "Smith", "username": "bsmith"},
            {"id": NO_NAME, "first_name": None, "last_name": None, "username": "shop.tablet"},
        ])
        conn.execute(tables["drafting"].insert(), [
            {"fab_id": 100, "drafter_id": JANE, "status": "drafting"},   # running
            {"fab_id": 101, "drafter_id": JANE, "status": "paused"},
            {"fab_id": 102, "drafter_id": JANE, "status": "on_hold"},
            {"fab_id": 103, "drafter_id": JANE, "status": "completed"},
        ])
        conn.execute(tables["cnc"].insert(), [{"fab_id": 200, "drafter_id": BOB, "status": "drafting"}])
        conn.execute(tables["final_programming"].insert(), [{"fab_id": 300, "user_id": NO_NAME, "status": "active"}])
        conn.execute(tables["slabsmith"].insert(), [
            {"fab_id": 400, "user_id": JANE, "status": "active"},
            {"fab_id": 401, "user_id": JANE, "status": "paused"},
        ])
        yield SimpleNamespace(execute=AsyncMock(side_effect=conn.execute))
    engine.dispose()


async def guard_message(db, *args, **kwargs):
    with pytest.raises(HTTPException) as error:
        await assert_no_running_timer_for_reassignment(db, *args, **kwargs)
    assert error.value.status_code == 409
    return error.value.detail


@pytest.mark.asyncio
async def test_running_timer_blocks_reassignment_and_names_who_runs_it(db):
    message = await guard_message(db, [100], ["drafting"], new_assignee_id=BOB)
    assert message == (
        "FAB #100 has a running Drafting timer started by Jane Doe. Stop the running timer before reassigning."
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("fab_ids, sections", [
    ([101, 102, 103], ["drafting"]),   # paused, on hold, completed
    ([401], ["slabsmith"]),            # paused
    ([200], ["drafting"]),             # CNC timer doesn't lock the drafting assignment
    ([999], ["drafting", "cnc", "final_programming", "slabsmith"]),
    ([], ["drafting"]),
])
async def test_non_running_or_other_stage_timers_do_not_block(db, fab_ids, sections):
    await assert_no_running_timer_for_reassignment(db, fab_ids, sections, new_assignee_id=BOB)


@pytest.mark.asyncio
async def test_reassigning_to_the_person_running_the_timer_is_allowed(db):
    await assert_no_running_timer_for_reassignment(db, [100], ["drafting"], new_assignee_id=JANE)


@pytest.mark.asyncio
async def test_each_stage_and_fallback_names(db):
    assert "running CNC Programming timer started by Bob Smith" in await guard_message(db, [200], ["cnc"], new_assignee_id=JANE)
    assert "running Final Programming timer started by shop.tablet" in await guard_message(db, [300], ["final_programming"], new_assignee_id=JANE)
    assert "running SlabSmith timer started by Jane Doe" in await guard_message(db, [400], ["slabsmith"], new_assignee_id=BOB)
    assert "running Revision timer" in await guard_message(db, [100], ["drafting"], new_assignee_id=BOB, labels={"drafting": "Revision"})


@pytest.mark.asyncio
async def test_bulk_reassignment_lists_every_blocked_fab(db):
    message = await guard_message(db, [100, 300, 101], ["drafting", "final_programming"], new_assignee_id=BOB)
    assert "FAB #100 has a running Drafting timer started by Jane Doe" in message
    assert "FAB #300 has a running Final Programming timer started by shop.tablet" in message
    assert "#101" not in message


# ── Each reassign endpoint runs the guard before saving ──────────────────────

def _result(first=None, scalar=None, rows=()):
    result = Mock()
    result.first.return_value = first
    result.scalar_one_or_none.return_value = scalar
    result.scalars.return_value.all.return_value = list(rows)
    return result


ITEM = {"scheduled_start_date": "2026-10-22T08:00:00", "scheduled_end_date": "2026-10-22T12:00:00",
        "total_sqft_required_to_draft": 40}


class _Blocked(Exception):
    pass


def _blocking_guard(calls):
    async def guard(db, fab_ids, sections, new_assignee_id=None, labels=None):
        calls.append((list(fab_ids), list(sections), new_assignee_id))
        raise _Blocked
    return guard


def _db(*results):
    queue = iter(results)
    return SimpleNamespace(execute=AsyncMock(side_effect=lambda *_: next(queue, _result(scalar=object()))),
                           commit=AsyncMock(), add=Mock(), refresh=AsyncMock())


USER = SimpleNamespace(id=9, is_super_admin=False)
ENDPOINTS = [
    # Bulk assign: also a reassignment when the FAB already has a drafter / programmer / operator
    (drafting, lambda db: drafting.create_drafting(
        drafting_data=drafting.DraftingCreateBulk(drafter_id=BOB, items=[{"fab_id": 100, **ITEM}, {"fab_id": 300, **ITEM}]),
        db=db, current_user=USER),
     lambda: _db(_result(scalar=object()), _result(rows=[object(), object()])),
     ([100, 300], ["drafting", "final_programming"], BOB)),
    (cnc, lambda db: cnc.create_cnc_drafting(
        drafting_data=CNCDraftingCreate(drafter_id=JANE, items=[{"fab_id": 200, **ITEM}]), db=db, current_user=USER),
     lambda: _db(_result(scalar=object()), _result(rows=[SimpleNamespace(id=200)]), _result(rows=[])),
     ([200], ["cnc"], JANE)),
    (slabsmith_sales_ct, lambda db: slabsmith_sales_ct.create_slabsmith(
        slabsmith_data=SlabSmithCreate(fab_id=400, slab_smith_type="AG", drafter_id=BOB, start_date="2026-10-22T08:00:00"),
        db=db, current_user=USER),
     lambda: _db(_result(scalar=object()), _result(scalar=object())),
     ([400], ["slabsmith"], BOB)),
    (drafting, lambda db: drafting.update_drafting(
        drafting_id=1, drafting_data=DraftingUpdate(drafter_id=BOB), db=db, current_user=USER),
     lambda: _db(_result(first=(SimpleNamespace(fab_id=100, drafter_id=JANE), SimpleNamespace(id=100)))),
     ([100], ["drafting", "final_programming"], BOB)),
    (cnc, lambda db: cnc.update_cnc_drafting(
        cnc_id=1, drafting_data=CNCDraftingUpdate(drafter_id=JANE), db=db, current_user=USER),
     lambda: _db(_result(first=(SimpleNamespace(fab_id=200, drafter_id=BOB), SimpleNamespace(id=200)))),
     ([200], ["cnc"], JANE)),
    (slabsmith_sales_ct, lambda db: slabsmith_sales_ct.update_slabsmith(
        slabsmith_id=1, slabsmith_data=SlabSmithUpdate(drafter_id=BOB), db=db, current_user=USER),
     lambda: _db(_result(scalar=SimpleNamespace(fab_id=400, drafter_id=JANE))),
     ([400], ["slabsmith"], BOB)),
    (final_programming, lambda db: final_programming.update_final_programming_record(
        fp_id=1, payload=FinalProgrammingUpdate(drafter_id=BOB), db=db, current_user=USER),
     lambda: _db(_result(scalar=SimpleNamespace(fab_id=300, drafter_id=JANE))),
     ([300], ["final_programming"], BOB)),
    (revisions, lambda db: revisions.update_revision(
        revision_id=1, update_data=RevisionUpdate(assigned_to=BOB), db=db, current_user=USER),
     lambda: _db(_result(scalar=SimpleNamespace(fab_id=100, assigned_to=JANE))),
     ([100], ["drafting"], BOB)),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("module, call, make_db, expected", ENDPOINTS, ids=[
    "POST /drafting", "POST /CNC", "POST /slabsmith",
    "PUT /drafting/{id}", "PUT /CNC/{id}", "PUT /slabsmith/{id}", "PUT /final-programming/{id}", "PUT /revisions/{id}",
])
async def test_reassign_endpoints_check_running_timers_before_saving(monkeypatch, module, call, make_db, expected):
    calls = []
    monkeypatch.setattr(module, "assert_no_running_timer_for_reassignment", _blocking_guard(calls))
    db = make_db()

    with pytest.raises(_Blocked):
        await call(db)

    assert calls == [expected]
    db.commit.assert_not_awaited()


def test_guard_covers_all_desk_stage_timers():
    assert set(timer_guards._RUNNING_FAB_TIMER_SOURCES) == {"drafting", "cnc", "final_programming", "slabsmith"}
