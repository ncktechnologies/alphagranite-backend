from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.app.interface.business_schemas import RevisionUpdate
from src.app.routers import revisions


@pytest.mark.asyncio
async def test_completing_a_revision_stamps_when_it_was_submitted():
    revision = SimpleNamespace(
        id=3, fab_id=9, assigned_to=None, actual_end_date=None, is_completed=False, revision_type="sales",
        requested_by=1, scheduled_start_date=None, scheduled_end_date=None, actual_start_date=None,
        revision_reason=None, revision_notes=None, department=None, person_name=None, status_id=1,
        created_at=datetime(2026, 10, 30), updated_at=None, updated_by=None, file_ids=None,
    )
    result = MagicMock()
    result.scalar_one_or_none.side_effect = [revision, None]
    db = SimpleNamespace(execute=AsyncMock(return_value=result), commit=AsyncMock(), refresh=AsyncMock())

    with patch.object(revisions, "notify_fab_event", AsyncMock()), \
         patch.object(revisions, "app_now", return_value=datetime(2026, 11, 2, 9, 30)):
        try:
            await revisions.update_revision(3, RevisionUpdate(is_completed=True), db, SimpleNamespace(id=4))
        except Exception:
            pass  # response building isn't under test

    assert revision.actual_end_date == datetime(2026, 11, 2, 9, 30)
