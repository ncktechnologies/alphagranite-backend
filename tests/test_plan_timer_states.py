from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app.database.shop_cut_plan import ShopCutPlan
from src.app.database.shop_cut_plan_timer_session import ShopCutPlanTimerSession
from src.app.routers import shop_cut_plan
from src.app.utils.helpers import APP_TZ

NOW = datetime(2026, 10, 21, 10, 0, tzinfo=APP_TZ)


def make_plan(plan_id, operator_id=5, estimated_hours=2.0):
    return ShopCutPlan(
        id=plan_id, fab_id=1, workstation_id=1, planning_section_id=7, user_id=operator_id,
        sequence=1, estimated_hours=estimated_hours, work_percentage=0, created_by=1,
    )


def make_session(session_id, plan_id, status, *, operator_id=5, work_seconds=0, run_start=None, created_minute=0):
    return ShopCutPlanTimerSession(
        id=session_id, shop_cut_plan_id=plan_id, operator_id=operator_id, status=status,
        session_start_at=datetime(2026, 10, 21, 8, 0), current_run_start_at=run_start,
        total_work_seconds=work_seconds, created_by=1,
        created_at=datetime(2026, 10, 21, 8, created_minute),
    )


@pytest.mark.asyncio
async def test_plan_timer_states_report_status_and_elapsed_seconds(monkeypatch):
    monkeypatch.setattr(shop_cut_plan, "app_now", lambda: NOW)
    engine = create_engine("sqlite://")
    try:
        ShopCutPlan.__table__.create(engine)
        ShopCutPlanTimerSession.__table__.create(engine)
        with Session(engine) as session:
            plans = [make_plan(plan_id) for plan_id in (1, 2, 3, 4, 5)]
            session.add_all(plans)
            session.add_all([
                # 1: running since 09:30 with 600s already banked -> 600 + 1800
                make_session(10, 1, "running", work_seconds=600, run_start=datetime(2026, 10, 21, 9, 30)),
                # 2: paused with 900s
                make_session(20, 2, "paused", work_seconds=900),
                # 3: one finished session
                make_session(30, 3, "stopped", work_seconds=1200),
                # 5: previous operator's paused session does not count as this plan's active timer
                make_session(50, 5, "paused", operator_id=99, work_seconds=300),
            ])
            session.commit()
            db = SimpleNamespace(execute=AsyncMock(side_effect=session.execute))

            states = await shop_cut_plan.get_plan_timer_states(db, plans)

        assert {plan_id: (s["status"], s["elapsed_seconds"], s["session_id"]) for plan_id, s in states.items()} == {
            1: ("running", 2400, 10),
            2: ("paused", 900, 20),
            3: ("stopped", 1200, None),
            4: ("idle", 0, None),
            5: ("stopped", 300, None),
        }
        assert db.execute.await_count == 3
    finally:
        engine.dispose()


@pytest.mark.asyncio
async def test_plan_timer_states_without_plans_skips_queries():
    db = SimpleNamespace(execute=AsyncMock())
    assert await shop_cut_plan.get_plan_timer_states(db, []) == {}
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("roles, shop_status_update, expected", [
    ([], False, False),
    (["Supervisor"], False, True),
    ([], True, True),
])
async def test_timer_control_allows_supervisors_and_shop_status_editors(monkeypatch, roles, shop_status_update, expected):
    checked = []

    async def fake_has_permission(db, user_id, menu, action):
        checked.append((user_id, menu, action))
        return shop_status_update

    monkeypatch.setattr(shop_cut_plan, "has_permission", fake_has_permission)
    result = SimpleNamespace(all=lambda: [(name,) for name in roles])
    db = SimpleNamespace(execute=AsyncMock(return_value=result))
    user = SimpleNamespace(id=7, is_super_admin=False)

    assert await shop_cut_plan._can_manage_shop_cut_plan_timer(db, user, make_plan(1, operator_id=5)) is expected
    assert checked == ([] if roles else [(7, "Shop Status", "update")])
