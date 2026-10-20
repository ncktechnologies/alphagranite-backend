from datetime import date, datetime

import pytest
from pydantic import ValidationError

from src.app.interface.business_schemas import TemplatingScheduleUpdate


def test_templating_update_accepts_logged_completion_payload():
    update = TemplatingScheduleUpdate.model_validate({
        "notes": ["Testing"],
        "actual_end_date": "2026-10-19T01:00:00",
        "schedule_start_date": "2026-10-20T01:00:00",
        "total_sqft": "52",
        "is_completed": True,
    })

    assert update.schedule_start_date == date(2026, 10, 20)
    assert update.actual_end_date == datetime(2026, 10, 19, 1)
    assert update.total_sqft == 52.0
    assert update.notes == ["Testing"]
    assert update.is_completed is True


@pytest.mark.parametrize("field", ["schedule_start_date", "schedule_due_date"])
@pytest.mark.parametrize("value", [
    "2026-10-20",
    "2026-10-20T01:00:00",
    "2026-10-20T01:00:00Z",
    "2026-10-20T01:00:00+14:00",
    date(2026, 10, 20),
    datetime(2026, 10, 20, 1),
])
def test_templating_schedule_updates_keep_supplied_calendar_date(field, value):
    update = TemplatingScheduleUpdate.model_validate({field: value})

    assert getattr(update, field) == date(2026, 10, 20)


@pytest.mark.parametrize("field", ["schedule_start_date", "schedule_due_date"])
def test_templating_schedule_updates_preserve_null_and_reject_invalid_dates(field):
    assert getattr(TemplatingScheduleUpdate.model_validate({field: None}), field) is None
    with pytest.raises(ValidationError):
        TemplatingScheduleUpdate.model_validate({field: "2026-02-30T01:00:00"})