from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.app.interface.business_schemas import FinalProgrammingSessionUpdate, SlabSmithSessionUpdate
from src.app.routers import final_programming, slabsmith


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