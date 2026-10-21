from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.app.routers.install_scheduling import _validate_shop_completion_for_install


@pytest.mark.asyncio
@pytest.mark.parametrize("fab_type", ["PUNCHOUT-AG", "PUNCHOUT-BILLABLE"])
async def test_punchout_fabs_bypass_shop_completion_check(fab_type):
    db = SimpleNamespace(execute=AsyncMock())

    await _validate_shop_completion_for_install(db, SimpleNamespace(id=10, fab_type=fab_type))

    db.execute.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "plan_count, percentage, expected_error",
    [
        (0, None, "reaches 100%"),
        (1, 99.99, "current: 99.99%"),
    ],
)
async def test_regular_fabs_still_require_shop_completion(plan_count, percentage, expected_error):
    result = SimpleNamespace(one=lambda: (plan_count, percentage))
    db = SimpleNamespace(execute=AsyncMock(return_value=result))

    with pytest.raises(HTTPException, match=expected_error) as raised:
        await _validate_shop_completion_for_install(db, SimpleNamespace(id=10, fab_type="STANDARD"))

    assert raised.value.status_code == 400
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_regular_fab_with_full_shop_completion_passes():
    result = SimpleNamespace(one=lambda: (3, 100.0))
    db = SimpleNamespace(execute=AsyncMock(return_value=result))

    await _validate_shop_completion_for_install(db, SimpleNamespace(id=10, fab_type="STANDARD"))

    db.execute.assert_awaited_once()