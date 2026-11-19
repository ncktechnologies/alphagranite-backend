from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from src.app.routers import reports
from src.app.utils.redo import ag_redo_revenue, apply_ag_redo_revenue, is_ag_redo


@pytest.mark.parametrize("cost, redo_sqft, total_sqft, expected", [
    (101.5, 58, None, -5887.0),
    (101.14, 58, 10, -5866.12),
    (101.5, 0, 58, -5887.0),      # older rows without redo_total_sqft use total_sqft
    (101.5, None, 58, -5887.0),
    (0, 58, None, 0.0),
    (None, 58, None, None),       # no cost entered -> leave revenue alone
    (101.5, 0, 0, None),          # nothing to price
])
def test_ag_redo_revenue(cost, redo_sqft, total_sqft, expected):
    assert ag_redo_revenue(cost, redo_sqft, total_sqft) == expected


def test_apply_keeps_revenue_when_it_cannot_be_priced():
    fab = SimpleNamespace(cost_per_sqft=None, redo_total_sqft=58, total_sqft=58, revenue=123.0)
    apply_ag_redo_revenue(fab)
    assert fab.revenue == 123.0


@pytest.mark.parametrize("fab_type, expected", [("AG REDO", True), (" ag redo ", True), ("STANDARD", False), (None, False)])
def test_is_ag_redo(fab_type, expected):
    assert is_ag_redo(fab_type) is expected


def _result(value=None):
    result = Mock()
    result.scalar_one_or_none.return_value = value
    result.first.return_value = None
    return result


@pytest.mark.asyncio
@pytest.mark.parametrize("patch, expected_revenue", [
    (reports.RedoPatchRequest(cost_per_sqft=101.5), -5887.0),
    (reports.RedoPatchRequest(cost_per_sqft=101.5, sqft=60), -6090.0),
    (reports.RedoPatchRequest(sqft=60), -6084.0),           # existing 101.4/sqft, new sq ft
    (reports.RedoPatchRequest(reason="Bracket removed"), 500.0),  # no cost/sq ft change -> untouched
])
async def test_redo_modal_submit_stores_negative_revenue(monkeypatch, patch, expected_revenue):
    fab = SimpleNamespace(
        id=15988, fab_type="AG REDO", cost_per_sqft=101.4, redo_total_sqft=58, total_sqft=58,
        revenue=500.0, cost_of_stone=None, cost_of_stone_id=None, stone_color_id=1, stone_type_id=1,
        no_of_pieces=1, redo_department=None, redo_requested_by=None, notes=None,
        updated_at=None, updated_by=None,
    )
    # First query loads the FAB; every later lookup (cost record, department, person) finds nothing.
    results = iter([_result(fab)])
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=lambda *_: next(results, _result())),
        get=AsyncMock(return_value=None),
        add=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
    )
    monkeypatch.setattr(reports, "success_response", lambda data, message: data)

    await reports.patch_redo_record(redo_id=15988, patch=patch, db=db, current_user=SimpleNamespace(id=1))

    assert fab.revenue == expected_revenue
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("existing_cost_of_stone", [None, 850.0])
async def test_redo_modal_submit_leaves_cost_of_stone_for_manual_entry(monkeypatch, existing_cost_of_stone):
    fab = SimpleNamespace(
        id=15988, fab_type="AG REDO", cost_per_sqft=None, redo_total_sqft=58, total_sqft=40,
        revenue=None, cost_of_stone=existing_cost_of_stone, cost_of_stone_id=None, stone_color_id=1,
        stone_type_id=1, no_of_pieces=1, redo_department=None, redo_requested_by=None, notes=None,
        updated_at=None, updated_by=None,
    )
    results = iter([_result(fab)])
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=lambda *_: next(results, _result())),
        get=AsyncMock(return_value=None), add=Mock(), flush=AsyncMock(), commit=AsyncMock(),
    )
    monkeypatch.setattr(reports, "success_response", lambda data, message: data)

    response = await reports.patch_redo_record(
        redo_id=15988, patch=reports.RedoPatchRequest(cost_per_sqft=101.5), db=db, current_user=SimpleNamespace(id=1),
    )

    assert fab.cost_of_stone == existing_cost_of_stone
    cost_record = next(call.args[0] for call in db.add.call_args_list if isinstance(call.args[0], reports.CostOfStone))
    assert cost_record.total_cost == "12362.70"   # 101.5 * 58 redo sq ft * 2.1, as on the Redos page
    assert response["total_cost"] == 12362.7
