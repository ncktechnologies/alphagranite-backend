import re
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.dialects import postgresql

from src.app.routers import reports


def _empty_result():
    result = Mock()
    result.all.return_value = []
    return result


async def _run_report(**dates):
    statements = []

    async def execute(statement, *_):
        statements.append(str(statement.compile(dialect=postgresql.dialect())))
        return _empty_result()

    db = SimpleNamespace(execute=AsyncMock(side_effect=execute))
    await reports.get_owner_installation_template_dashboard_report(
        search=None, fab_type=None, sales_person_id=None, db=db, current_user=SimpleNamespace(id=1), **dates,
    )
    return statements


@pytest.mark.asyncio
@pytest.mark.parametrize("table", ["installer_job_timer_sessions", "templater_job_timer_sessions"])
async def test_date_range_filters_each_session_before_totals(table):
    """A job shows when any session started in range, and only those sessions are summed."""
    statements = await _run_report(from_date=date(2026, 10, 1), to_date=date(2026, 10, 1))
    report_sql = next(s for s in statements if f"FROM {table}" in s)

    subquery = report_sql[report_sql.index(f"FROM {table}"):report_sql.index("GROUP BY")]
    assert re.search(rf"{table}\.session_start_at >= ", subquery)
    assert re.search(rf"{table}\.session_start_at <= ", subquery)
    # The job's latest activity date is no longer what decides whether it shows.
    assert "activity_date >=" not in report_sql
    assert "activity_date <=" not in report_sql


@pytest.mark.asyncio
async def test_no_date_range_keeps_all_sessions():
    statements = await _run_report(from_date=None, to_date=None)
    assert not any("session_start_at >=" in s or "session_start_at <=" in s for s in statements)
