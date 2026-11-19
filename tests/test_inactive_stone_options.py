from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from src.app.database.stone_color import StoneColor
from src.app.database.stone_type import StoneType
from src.app.interface.business_schemas import FabUpdate
from src.app.routers import fabs

ACTIVE, INACTIVE = 1, 2


@pytest.mark.parametrize("option", [None, SimpleNamespace(name="Granite", status_id=ACTIVE)])
def test_active_or_missing_option_passes(option):
    fabs._assert_active_stone_option(option, "stone type")


def test_inactive_option_is_rejected_by_name():
    with pytest.raises(HTTPException) as error:
        fabs._assert_active_stone_option(SimpleNamespace(name="Calacatta Old", status_id=INACTIVE), "stone color")
    assert error.value.status_code == 400
    assert error.value.detail["message"] == 'The stone color "Calacatta Old" is inactive. Choose an active stone color.'


def _update_db(fab, options, payload):
    """execute() order in update_fab: the FAB, then the sent stone type, then the sent stone color."""
    def result(value):
        r = Mock()
        r.scalar_one_or_none.return_value = value
        return r
    lookups = [fab]
    if payload.get("stone_type_id"):
        lookups.append(options.get((StoneType, payload["stone_type_id"])))
    if payload.get("stone_color_id"):
        lookups.append(options.get((StoneColor, payload["stone_color_id"])))
    queue = iter([result(value) for value in lookups])
    return SimpleNamespace(
        execute=AsyncMock(side_effect=lambda *_: next(queue)),
        get=AsyncMock(side_effect=lambda model, option_id: options.get((model, option_id))),
        add=Mock(), commit=AsyncMock(), refresh=AsyncMock(),
    )


@pytest.fixture
def fab():
    return SimpleNamespace(
        id=7, stone_type_id=1, stone_color_id=10, current_stage="drafting", fab_type="STANDARD",
        drafter_id=None, drafting_needed=True, slab_smith_ag_needed=False, slab_smith_cust_needed=False,
        updated_at=None, updated_by=None,
    )


OPTIONS = {
    (StoneType, 1): SimpleNamespace(name="Quartz", status_id=INACTIVE),
    (StoneType, 2): SimpleNamespace(name="Granite", status_id=ACTIVE),
    (StoneColor, 10): SimpleNamespace(name="Old White", status_id=INACTIVE, stone_type_id=None),
    (StoneColor, 11): SimpleNamespace(name="Calacatta Old", status_id=INACTIVE, stone_type_id=None),
    (StoneColor, 12): SimpleNamespace(name="Absolute Black", status_id=ACTIVE, stone_type_id=None),
}


@pytest.mark.asyncio
@pytest.mark.parametrize("payload, message", [
    (dict(stone_color_id=11), 'The stone color "Calacatta Old" is inactive'),
    (dict(stone_type_id=1, stone_color_id=12), None),   # type unchanged (already inactive) -> allowed
    (dict(stone_type_id=2, stone_color_id=11), 'The stone color "Calacatta Old" is inactive'),
])
async def test_update_blocks_switching_to_inactive_stone(monkeypatch, fab, payload, message):
    db = _update_db(fab, OPTIONS, payload)
    monkeypatch.setattr(fabs, "get_fab", AsyncMock(return_value="updated"))

    if message:
        with pytest.raises(HTTPException) as error:
            await fabs.update_fab(fab_id=7, fab_data=FabUpdate(**payload), db=db, current_user=SimpleNamespace(id=1))
        assert error.value.detail["message"].startswith(message)
        db.commit.assert_not_awaited()
    else:
        assert await fabs.update_fab(fab_id=7, fab_data=FabUpdate(**payload), db=db, current_user=SimpleNamespace(id=1)) == "updated"
        db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_update_keeps_unchanged_inactive_values(monkeypatch, fab):
    """Saving other fields of a FAB whose type/color later went inactive still works via the API."""
    payload = dict(stone_type_id=1, stone_color_id=10, input_area="KITCHEN")
    db = _update_db(fab, OPTIONS, payload)
    monkeypatch.setattr(fabs, "get_fab", AsyncMock(return_value="updated"))

    assert await fabs.update_fab(fab_id=7, fab_data=FabUpdate(**payload), db=db, current_user=SimpleNamespace(id=1)) == "updated"
    db.get.assert_not_awaited()
