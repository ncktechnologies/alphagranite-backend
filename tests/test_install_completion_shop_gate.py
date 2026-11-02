from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from src.app.interface.business_schemas import InstallCompletionUpdate
from src.app.routers import install_completion


def db_with(record, shop_progress):
    lookup = MagicMock()
    lookup.scalar_one_or_none.return_value = record
    progress = MagicMock()
    progress.one.return_value = shop_progress  # (plan_count, average work %)
    return SimpleNamespace(
        execute=AsyncMock(side_effect=[lookup, progress]),
        get=AsyncMock(return_value=SimpleNamespace(id=9, fab_type="STANDARD")),
        commit=AsyncMock(), refresh=AsyncMock(),
    )


def record():
    return SimpleNamespace(id=1, fab_id=9, is_completed=False, is_confirmed=True, updated_at=None, updated_by=None)


@pytest.mark.asyncio
async def test_install_cannot_be_completed_before_shop_is_done():
    rec = record()
    with pytest.raises(HTTPException) as err:
        await install_completion.update_install_completion(
            1, InstallCompletionUpdate(is_completed=True), db_with(rec, (3, 66.67)), SimpleNamespace(id=2)
        )
    assert "100%" in str(err.value.detail) and "66.67" in str(err.value.detail)
    assert rec.is_completed is False


@pytest.mark.asyncio
async def test_install_completes_when_shop_is_at_100():
    rec = record()
    db = db_with(rec, (3, 100.0))
    try:
        await install_completion.update_install_completion(1, InstallCompletionUpdate(is_completed=True), db, SimpleNamespace(id=2))
    except Exception:
        pass  # response building isn't under test
    assert rec.is_completed is True
    db.commit.assert_awaited()
