import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlmodel.sql.sqltypes import UTCDateTime

import src.app.routers.fabs as fabs
from src.app.database.templating import Templating
from src.app.utils.helpers import APP_TZ


def _sql(query) -> str:
    return str(query.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


def test_date_filters_compare_the_scheduled_calendar_day(monkeypatch):
    monkeypatch.setattr(fabs, "app_today", lambda: date(2026, 10, 7))  # a Wednesday
    base = select(Templating.fab_id)

    last_week = _sql(fabs._apply_date_filter(base, "last_week"))
    assert "CAST(templatings.schedule_start_date AS DATE) BETWEEN '2026-09-28' AND '2026-10-04'" in last_week

    last_month = _sql(fabs._apply_date_filter(base, "last_month"))
    assert "BETWEEN '2026-09-01' AND '2026-09-30'" in last_month

    today = _sql(fabs._apply_date_filter(base, "today"))
    assert "CAST(templatings.schedule_start_date AS DATE) = '2026-10-07'" in today


def test_datetime_columns_accept_plain_dates_as_midnight():
    bound = UTCDateTime().process_bind_param(date(2026, 9, 28), None)
    assert bound == datetime(2026, 9, 28, tzinfo=APP_TZ)
    assert UTCDateTime().process_bind_param(None, None) is None
