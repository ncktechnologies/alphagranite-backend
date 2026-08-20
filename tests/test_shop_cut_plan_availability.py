import os
from datetime import datetime

import pytest
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
