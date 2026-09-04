import os
from datetime import datetime

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from starlette.datastructures import QueryParams

os.environ.setdefault("SECRET_KEY", "testsecretkey")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

pytest.importorskip("aiosqlite")
pytest.importorskip("jwt")

from src.app.routers.shop_cut_plan import (
    _apply_shop_plan_filters,
    _build_shop_plans_query,
    _compute_business_rollover_end,
    _parse_multi_int_query_param,
)
from src.app.database.fab import Fab
from src.app.routers.fabs import _active_shop_cut_plan_visibility_filter


class _RequestStub:
    def __init__(self, query_string: str):
        self.query_params = QueryParams(query_string)


def test_compute_business_rollover_end_spills_to_next_day():
    start = datetime(2026, 4, 1, 14, 0)

    result = _compute_business_rollover_end(start, 6)

    assert result == datetime(2026, 4, 2, 11, 0)


def test_compute_business_rollover_end_skips_lunch_and_next_day():
    start = datetime(2026, 4, 1, 11, 0)

    result = _compute_business_rollover_end(start, 8)

    assert result == datetime(2026, 4, 2, 11, 0)


def test_parse_multi_int_query_param_accepts_repeated_values():
    request = _RequestStub("workstation_id=1&workstation_id=2&workstation_id=1")

    result = _parse_multi_int_query_param(request, "workstation_id")

    assert result == [1, 2]


def test_apply_shop_plan_filters_uses_in_for_multi_value_filters():
    query = _apply_shop_plan_filters(
        _build_shop_plans_query(),
        fab_id=None,
        search_fab_id=None,
        fab_type=None,
        workstation_id=[1, 2],
        planning_section_id=[3, 4],
        operator_id=[5, 6],
        status_id=None,
        cut_type=None,
        search=None,
        type=None,
    )

    compiled_query = str(query.compile(compile_kwargs={"literal_binds": True}))

    assert "shop_cut_plans.workstation_id IN (1, 2)" in compiled_query
    assert "shop_cut_plans.planning_section_id IN (3, 4)" in compiled_query
    assert "shop_cut_plans.user_id IN (5, 6)" in compiled_query


@pytest.mark.asyncio
async def test_completed_shop_plans_remain_visible_until_shop_estimate_is_set():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.execute(text("""
            CREATE TABLE fabs (
                id INTEGER PRIMARY KEY,
                current_stage VARCHAR,
                cutlist_complete BOOLEAN,
                shop_est_completion_date DATETIME
            )
        """))
        await connection.execute(text("""
            CREATE TABLE shop_cut_plans (
                id INTEGER PRIMARY KEY,
                fab_id INTEGER,
                work_percentage INTEGER
            )
        """))
        await connection.execute(text("""
            INSERT INTO fabs VALUES
                (1, 'shop', 1, NULL),
                (2, 'shop', 1, '2026-09-04 12:00:00'),
                (3, 'shop', 1, '2026-09-04 12:00:00')
        """))
        await connection.execute(text("""
            INSERT INTO shop_cut_plans VALUES
                (1, 1, 100),
                (2, 2, 100),
                (3, 3, 75)
        """))

    async with AsyncSession(engine) as session:
        visible_fab_ids = (
            await session.execute(
                select(Fab.id)
                .where(_active_shop_cut_plan_visibility_filter())
                .order_by(Fab.id)
            )
        ).scalars().all()

    await engine.dispose()
    assert visible_fab_ids == [1, 3]
