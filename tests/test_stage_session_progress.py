from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from pydantic import ValidationError

from src.app.interface.business_schemas import (
    CNCDraftingSessionAction, DraftingSessionAction, FinalProgrammingSessionUpdate, SlabSmithSessionUpdate,
)
from src.app.routers import cnc, drafting, final_programming, slabsmith
from src.app.utils.helpers import APP_TZ


class QueryResult:
    def __init__(self, *, scalar=None, rows=None):
        self._scalar = scalar
        self._rows = rows or []

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return self

    def all(self):
        return self._rows

    def first(self):
        return self._scalar if self._scalar is not None else next(iter(self._rows), None)


class QueuedSession:
    def __init__(self, results):
        self._results = iter(results)

    async def execute(self, statement):
        return next(self._results)


@pytest.mark.parametrize("schema", [FinalProgrammingSessionUpdate, SlabSmithSessionUpdate])
def test_stage_session_request_accepts_valid_work_percentage(schema):
    payload = schema(action="pause", sqft_completed=42.5, work_percentage_done=65.5)

    assert payload.work_percentage_done == 65.5

    with pytest.raises(ValidationError):
        schema(action="pause", work_percentage_done=101)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_handler",
    [final_programming.get_session_status, slabsmith.get_slabsmith_session_status],
)
async def test_stage_session_status_returns_latest_non_null_progress(status_handler):
    session = SimpleNamespace(
        id=11,
        status="active",
        session_start_time=datetime.now() - timedelta(minutes=5),
        current_pause_start_time=None,
        total_pause_duration=0,
    )
    newest_note = SimpleNamespace(sqft_completed=None, work_percentage_done=65.5)
    older_note = SimpleNamespace(sqft_completed=42.5, work_percentage_done=40.0)
    db = QueuedSession(
        [
            QueryResult(scalar=session),
            QueryResult(rows=[newest_note, older_note]),
        ]
    )

    response = await status_handler(
        fab_id=7,
        db=db,
        current_user=SimpleNamespace(id=3),
    )

    assert response["data"]["sqft_completed"] == 42.5
    assert response["data"]["work_percentage_done"] == 65.5


@pytest.mark.asyncio
@pytest.mark.parametrize("end_field", ["session_end_time", "timestamp"])
@pytest.mark.parametrize("end_value", [
    "2026-10-17T10:00:00", "2026-10-17T10:00:00-05:00", "2026-10-17T15:00:00Z",
])
@pytest.mark.parametrize("paused", [False, True])
@pytest.mark.parametrize("router, handler, schema", [
    (cnc, cnc.manage_cnc_session, CNCDraftingSessionAction),
    (drafting, drafting.manage_drafting_session, DraftingSessionAction),
])
async def test_session_end_normalizes_client_datetimes(
    monkeypatch, end_field, end_value, paused, router, handler, schema,
):
    end_time = datetime(2026, 10, 17, 10, tzinfo=APP_TZ)
    monkeypatch.setattr(router, "app_now", lambda: end_time)
    session = SimpleNamespace(
        id=11, fab_id=7, drafter_id=3, status="paused" if paused else "drafting",
        session_start_time=datetime(2026, 10, 17, 9, tzinfo=APP_TZ),
        current_pause_start_time=datetime(2026, 10, 17, 9, 50) if paused else None,
        total_pause_duration=60, total_time_spent=0,
        cumulative_sqft_drafted="10", work_percentage_done=50,
    )
    db = QueuedSession([
        QueryResult(scalar=object()), QueryResult(scalar=object()),
        QueryResult(scalar=session), QueryResult(rows=[]),
    ])
    db.add = Mock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    payload = schema(action="end", drafter_id=3, **{end_field: end_value})

    response = await handler(
        fab_id=7, session_data=payload, db=db, current_user=SimpleNamespace(id=3),
    )

    assert session.status == "completed"
    assert session.session_end_time == end_time
    assert session.session_end_time.tzinfo is not None
    assert session.total_pause_duration == (660 if paused else 60)
    assert session.total_time_spent == (2940 if paused else 3540)
    assert response["data"].total_time_spent == session.total_time_spent
    db.commit.assert_awaited_once()