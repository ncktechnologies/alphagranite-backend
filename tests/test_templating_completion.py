from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.app.interface.business_schemas import TemplatingCompleteRequest, TemplatingScheduleUpdate
from src.app.routers import templating


class QueryResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


def make_templating_record():
    return SimpleNamespace(
        id=42,
        fab_id=24,
        technician_id=None,
        status_id=1,
        schedule_start_date=None,
        schedule_due_date=None,
        total_sqft=None,
        actual_start_date=None,
        actual_end_date=None,
        duration=None,
        notes=[],
        review_checklist=None,
        is_templating_schedule=True,
        rescheduled=False,
        is_completed=False,
        created_at=None,
        updated_at=None,
        updated_by=None,
    )


def make_templating_fab():
    return SimpleNamespace(
        id=24,
        current_stage="templating",
        next_stage="pre_draft_review",
        drafting_needed=True,
        slab_smith_ag_needed=False,
        slab_smith_cust_needed=False,
        template_review_complete=False,
        template_completed_date=None,
        updated_at=None,
        updated_by=None,
    )


def make_mock_db(record, fab):
    return SimpleNamespace(
        execute=AsyncMock(side_effect=[QueryResult(record), QueryResult(fab)]),
        commit=AsyncMock(),
        refresh=AsyncMock(),
        get=AsyncMock(return_value=SimpleNamespace(name="Completed")),
    )


@pytest.mark.parametrize(
    "drafting_needed, expected_next_stage",
    [(True, "drafting"), (False, "sales_ct")],
)
def test_mark_templating_complete_sets_flag_and_advances_stage(
    monkeypatch, drafting_needed, expected_next_stage,
):
    timestamp = datetime(2026, 10, 21, 12, tzinfo=timezone.utc)
    monkeypatch.setattr(templating, "app_now", lambda: timestamp)
    record = SimpleNamespace(
        is_completed=False,
        status_id=1,
        actual_end_date=None,
        updated_at=None,
        updated_by=None,
    )
    fab = SimpleNamespace(
        current_stage="templating",
        next_stage="pre_draft_review",
        drafting_needed=drafting_needed,
        slab_smith_ag_needed=False,
        slab_smith_cust_needed=False,
        template_review_complete=False,
        template_completed_date=None,
        updated_at=None,
        updated_by=None,
    )

    templating._mark_templating_complete(record, fab, user_id=17)

    assert record.is_completed is True
    assert record.status_id == 2
    assert record.actual_end_date == timestamp
    assert record.updated_at == timestamp
    assert record.updated_by == 17
    assert fab.current_stage == "pre_draft_review"
    assert fab.next_stage == expected_next_stage
    assert fab.template_review_complete is True
    assert fab.template_completed_date == timestamp
    assert fab.updated_at == timestamp
    assert fab.updated_by == 17


def test_mark_templating_complete_does_not_advance_an_already_advanced_fab(monkeypatch):
    timestamp = datetime(2026, 10, 21, 12, tzinfo=timezone.utc)
    earlier = datetime(2026, 10, 20, 12, tzinfo=timezone.utc)
    monkeypatch.setattr(templating, "app_now", lambda: timestamp)
    record = SimpleNamespace(
        is_completed=True,
        status_id=2,
        actual_end_date=earlier,
        updated_at=None,
        updated_by=None,
    )
    fab = SimpleNamespace(
        current_stage="drafting",
        next_stage="sales_ct",
        drafting_needed=True,
        slab_smith_ag_needed=False,
        slab_smith_cust_needed=False,
        template_review_complete=True,
        template_completed_date=earlier,
        updated_at=None,
        updated_by=None,
    )

    templating._mark_templating_complete(record, fab, user_id=17)

    assert fab.current_stage == "drafting"
    assert fab.next_stage == "sales_ct"
    assert record.actual_end_date == earlier
    assert fab.template_completed_date == earlier


def test_mark_templating_complete_handles_missing_fab(monkeypatch):
    timestamp = datetime(2026, 10, 21, 12, tzinfo=timezone.utc)
    monkeypatch.setattr(templating, "app_now", lambda: timestamp)
    record = SimpleNamespace(
        is_completed=False,
        status_id=1,
        actual_end_date=None,
        updated_at=None,
        updated_by=None,
    )

    templating._mark_templating_complete(record, None, user_id=17)

    assert record.is_completed is True
    assert record.status_id == 2
    assert record.actual_end_date == timestamp


@pytest.mark.asyncio
async def test_update_templating_completion_advances_fab_in_response(monkeypatch):
    timestamp = datetime(2026, 10, 21, 12, tzinfo=timezone.utc)
    monkeypatch.setattr(templating, "app_now", lambda: timestamp)
    record = make_templating_record()
    fab = make_templating_fab()
    db = make_mock_db(record, fab)

    response = await templating.update_templating(
        templating_id=record.id,
        update_data=TemplatingScheduleUpdate(is_completed=True),
        db=db,
        current_user=SimpleNamespace(id=17),
    )

    assert response["data"].is_completed is True
    assert response["data"].current_stage == "pre_draft_review"
    assert response["data"].next_stage == "drafting"
    assert record.status_id == 2
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_complete_templating_sets_completion_flag_and_advances_fab(monkeypatch):
    timestamp = datetime(2026, 10, 21, 12, tzinfo=timezone.utc)
    monkeypatch.setattr(templating, "app_now", lambda: timestamp)
    record = make_templating_record()
    fab = make_templating_fab()
    db = make_mock_db(record, fab)

    response = await templating.complete_templating(
        templating_id=record.id,
        request_data=TemplatingCompleteRequest(),
        db=db,
        current_user=SimpleNamespace(id=17),
    )

    assert response["data"].is_completed is True
    assert response["data"].current_stage == "pre_draft_review"
    assert response["data"].next_stage == "drafting"
    assert record.status_id == 2
    db.commit.assert_awaited_once()