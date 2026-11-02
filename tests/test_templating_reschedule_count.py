from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.app.interface.business_schemas import TemplatingScheduleUpdate
from src.app.routers import templating as templating_router


def make_db(record):
    result = MagicMock()
    result.scalar_one_or_none.return_value = record
    return SimpleNamespace(
        execute=AsyncMock(return_value=result), get=AsyncMock(return_value=None),
        commit=AsyncMock(), refresh=AsyncMock(),
    )


def record():
    return SimpleNamespace(
        id=1, fab_id=10, technician_id=None, schedule_start_date=None, schedule_due_date=None,
        total_sqft=None, actual_start_date=None, actual_end_date=None, duration=None, notes=None,
        is_templating_schedule=True, is_completed=None, rescheduled=False, reschedule_count=0,
        status_id=1, created_at=datetime(2026, 11, 1), updated_at=None, updated_by=None,
        current_stage="templating", next_stage=None,  # also stands in for the fab lookup
    )


@pytest.mark.asyncio
async def test_each_reschedule_increments_count_without_limit():
    rec = record()
    db = make_db(rec)
    user = SimpleNamespace(id=4)
    with patch.object(templating_router, "_sync_fab_total_sqft", AsyncMock()):
        for _ in range(3):
            await templating_router.update_templating(
                1, TemplatingScheduleUpdate(is_completed=False, reschedule=True), db, user
            )
    assert rec.reschedule_count == 3
    assert rec.rescheduled is True


@pytest.mark.asyncio
async def test_undoing_completion_is_not_a_reschedule():
    rec = record()
    with patch.object(templating_router, "_sync_fab_total_sqft", AsyncMock()):
        await templating_router.update_templating(1, TemplatingScheduleUpdate(is_completed=False), make_db(rec), SimpleNamespace(id=4))
    assert rec.reschedule_count == 0
