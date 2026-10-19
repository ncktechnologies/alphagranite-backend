import os
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

os.environ.setdefault("SECRET_KEY", "testsecretkey")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

pytest.importorskip("aiosqlite")
pytest.importorskip("jwt")

from src.app.database.shop_cut_plan import ShopCutPlan
from src.app.database.shop_cut_plan_timer_session import ShopCutPlanTimerSession
from src.app.routers.shop_cut_plan import (
    _fetch_by_ids,
    _get_work_progress_by_plan,
    _recalculate_shop_plan_work_percentage,
)
from src.app.utils.helpers import to_app_tz


def _plan(plan_id: int, estimated_hours: float, work_percentage: int = 0) -> ShopCutPlan:
    return ShopCutPlan(
        id=plan_id,
        fab_id=1,
        workstation_id=1,
        planning_section_id=1,
        user_id=1,
        created_by=1,
        sequence=1,
        estimated_hours=estimated_hours,
        work_percentage=work_percentage,
        scheduled_start_date=datetime(2026, 10, 12, 8, 0),
    )


def _session(session_id: int, plan_id: int, status: str, total_work_seconds: int, run_start=None):
    return ShopCutPlanTimerSession(
        id=session_id,
        shop_cut_plan_id=plan_id,
        operator_id=1,
        created_by=1,
        status=status,
        session_start_at=datetime(2026, 10, 12, 8, 0),
        current_run_start_at=run_start,
        total_work_seconds=total_work_seconds,
    )


@pytest.mark.asyncio
async def test_batched_work_progress_matches_per_plan_recalculation():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(
            SQLModel.metadata.create_all,
            tables=[ShopCutPlan.__table__, ShopCutPlanTimerSession.__table__],
        )

    plans = [
        _plan(1, estimated_hours=4),                       # stored seconds only
        _plan(2, estimated_hours=2),                       # stored + running session
        _plan(3, estimated_hours=8, work_percentage=40),   # no timer data -> manual percentage
        _plan(4, estimated_hours=1),                       # over estimate -> capped at 100
    ]
    async with AsyncSession(engine) as session:
        session.add_all([
            _session(1, 1, "stopped", 3600),
            _session(2, 1, "stopped", 1800),
            _session(3, 2, "stopped", 600),
            _session(4, 2, "running", 300, run_start=datetime(2026, 10, 14, 9, 0)),
            _session(5, 4, "stopped", 7200),
        ])
        await session.commit()

        as_of = to_app_tz(datetime(2026, 10, 14, 9, 30))
        batched = await _get_work_progress_by_plan(session, plans, as_of)
        for plan in plans:
            expected = await _recalculate_shop_plan_work_percentage(session, plan, as_of)
            assert batched[plan.id] == expected

    await engine.dispose()
    assert batched[1] == (37, 1.5, 5400)
    assert batched[2] == (37, 0.75, 2700)
    assert batched[3] == (40, 0.0, 0)
    assert batched[4] == (100, 2.0, 7200)


@pytest.mark.asyncio
async def test_fetch_by_ids_ignores_none_and_missing_ids():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all, tables=[ShopCutPlan.__table__])

    async with AsyncSession(engine) as session:
        session.add_all([_plan(1, estimated_hours=4), _plan(2, estimated_hours=6)])
        await session.commit()

        by_id = await _fetch_by_ids(session, ShopCutPlan, [1, None, 1, 99])
        empty = await _fetch_by_ids(session, ShopCutPlan, [None])

    await engine.dispose()
    assert {plan_id: plan.estimated_hours for plan_id, plan in by_id.items()} == {1: 4}
    assert empty == {}
