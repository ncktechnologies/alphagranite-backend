import os
from datetime import date, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

os.environ.setdefault("SECRET_KEY", "testsecretkey")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

pytest.importorskip("aiosqlite")

from src.app.routers.reports import (
    _INSTALLER_METRIC_KEYS,
    _blank_installer_week_row,
    _hcp_active_employee_count_for_month,
    _hcp_weekly_labor_totals,
    _installer_period_totals,
    _week_ending_for_period,
    _week_windows_for_month,
)
from src.app.service.hcp_payroll_ingestion import pay_period_for_pull

FRIDAY = 4


async def _create_tables(connection) -> None:
    await connection.execute(text("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username VARCHAR(255),
            hcp_employee_id VARCHAR(255)
        )
    """))
    await connection.execute(text("""
        CREATE TABLE hcp_payroll_report_snapshots (
            id INTEGER PRIMARY KEY,
            source_config_id INTEGER NOT NULL,
            ingestion_run_id INTEGER NOT NULL,
            report_settings_id VARCHAR(100) NOT NULL,
            period_start DATE,
            period_end DATE,
            created_at DATETIME NOT NULL
        )
    """))
    await connection.execute(text("""
        CREATE TABLE hcp_payroll_report_rows (
            id INTEGER PRIMARY KEY,
            snapshot_id INTEGER NOT NULL,
            source_config_id INTEGER NOT NULL,
            ingestion_run_id INTEGER NOT NULL,
            row_kind VARCHAR(50) NOT NULL,
            row_index INTEGER NOT NULL,
            cost_center_name VARCHAR(255),
            employee_id VARCHAR(100),
            employee_first_name VARCHAR(255),
            employee_last_name VARCHAR(255),
            hourly_pay FLOAT,
            regular_hours FLOAT,
            holiday_hours FLOAT,
            pto_hours FLOAT,
            total_reg_pto_hol_wages FLOAT,
            overtime_hours FLOAT,
            total_ot_wages FLOAT,
            raw_line_text VARCHAR,
            created_at DATETIME
        )
    """))
    await connection.execute(text("""
        CREATE TABLE hcp_staff_roster_snapshots (
            id INTEGER PRIMARY KEY,
            source_config_id INTEGER NOT NULL,
            ingestion_run_id INTEGER NOT NULL,
            report_settings_id VARCHAR(100) NOT NULL,
            pulled_at DATETIME NOT NULL,
            active_employee_count INTEGER NOT NULL,
            period_start DATE,
            period_end DATE
        )
    """))


async def _seed_db() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await _create_tables(connection)

        await connection.execute(text("""
            INSERT INTO users (id, username, hcp_employee_id) VALUES (1, 'jhernandez', '247')
        """))

        await connection.execute(text("""
            INSERT INTO hcp_payroll_report_snapshots
                (id, source_config_id, ingestion_run_id, report_settings_id, period_start, period_end, created_at)
            VALUES
                -- Monday pull for pay week Sep 7-13 -> report week ending Fri Sep 11.
                (1, 1, 1, '89798180', '2026-09-07', '2026-09-13', '2026-09-14 00:00:00'),
                -- Two pulls for pay week Sep 14-20 -> report week ending Fri Sep 18; the later pull (3) wins.
                (2, 1, 1, '89798180', '2026-09-14', '2026-09-20', '2026-09-21 00:00:00'),
                (3, 1, 1, '89798180', '2026-09-14', '2026-09-20', '2026-09-21 12:00:00'),
                -- Legacy snapshot without a stored period: derived from the Mon Aug 31 pull -> week ending Fri Aug 28.
                (4, 1, 1, '89798180', NULL, NULL, '2026-08-31 00:00:00'),
                -- Previous year's pull -- must not appear in a 2026 report.
                (5, 1, 1, '89798180', '2025-09-15', '2025-09-21', '2025-09-22 00:00:00')
        """))
        await connection.execute(
            text("""
                INSERT INTO hcp_payroll_report_rows
                    (id, snapshot_id, source_config_id, ingestion_run_id, row_kind, row_index, cost_center_name,
                     employee_id, employee_first_name, employee_last_name, regular_hours, holiday_hours,
                     overtime_hours, total_reg_pto_hol_wages, total_ot_wages)
                VALUES
                    (1, 1, 1, 1, 'detail', 1, 'Install-Omar', '285', 'Omar', 'Hernandez', 40.0, 0.0, 10.0, 1180.0, 442.5),
                    -- Superseded re-pull of the Sep 14-20 week.
                    (2, 2, 1, 1, 'detail', 1, 'Install-Old', '999', 'Old', 'Guy', 1, 0, 0, 1, 0),
                    -- Employee 247 split across two Install cost centers -> must combine into one head.
                    (3, 3, 1, 1, 'detail', 1, 'Install-Omar', '247', 'Jose', 'Hernandez', 24.21, 40.0, 17.43, 968.4, 17.43),
                    (4, 3, 1, 1, 'detail', 2, 'Install Tony', '247', 'Jose', 'Hernandez', 10.0, 0.0, 0.0, 100.0, 0.0),
                    -- Legacy row without employee_id -> dedup falls back to name.
                    (5, 3, 1, 1, 'detail', 3, 'Install-General', NULL, 'Roger', 'Olivo', 19.5, 40.0, 16.24, 475.02, 16.24),
                    -- Fabrication row -- must not be counted in Install totals.
                    (6, 3, 1, 1, 'detail', 4, 'Fabrication', '54', 'Jose', 'Corona', 18.0, 40.0, 9.96, 720.0, 9.96),
                    -- Subtotal row -- must be excluded from all totals.
                    (7, 3, 1, 1, 'subtotal', 5, 'Install-General', NULL, NULL, NULL, 999, NULL, 999, 999, 999),
                    (8, 4, 1, 1, 'detail', 1, 'Install Jose S', '41', 'Jose', 'Sandoval', 40.0, 0.0, 17.39, 1600.0, 1043.4),
                    (9, 5, 1, 1, 'detail', 1, 'Install Jose S', '41', 'Jose', 'Sandoval', 40.0, 0.0, 0.0, 1500.0, 0.0)
            """)
        )

        await connection.execute(text("""
            INSERT INTO hcp_staff_roster_snapshots
                (id, source_config_id, ingestion_run_id, report_settings_id, pulled_at, active_employee_count, period_start, period_end)
            VALUES
                (1, 1, 1, '93428419', '2026-09-07 00:00:00', 5, '2026-08-31', '2026-09-06'),
                (2, 1, 1, '93428419', '2026-09-21 00:00:00', 39, '2026-09-14', '2026-09-20'),
                (3, 1, 1, '93428419', '2026-10-05 00:00:00', 50, '2026-09-28', '2026-10-04')
        """))

    return AsyncSession(engine, expire_on_commit=False)


@pytest.mark.parametrize(
    ("pulled_at", "expected"),
    [
        # Scheduled Monday-midnight pull covers the previous Mon-Sun week.
        (datetime(2026, 9, 28, 0, 0), (date(2026, 9, 21), date(2026, 9, 27))),
        # Ad-hoc mid-week and Sunday pulls fall back to the last completed week.
        (datetime(2026, 9, 25, 11, 27), (date(2026, 9, 14), date(2026, 9, 20))),
        (datetime(2026, 9, 27, 23, 59), (date(2026, 9, 14), date(2026, 9, 20))),
    ],
)
def test_pay_period_for_pull(pulled_at, expected):
    assert pay_period_for_pull(pulled_at) == expected


def test_week_windows_for_month_do_not_overlap():
    windows = _week_windows_for_month(2026, 8, FRIDAY)

    assert [w["week_end"] for w in windows] == [
        date(2026, 8, 7), date(2026, 8, 14), date(2026, 8, 21), date(2026, 8, 28), date(2026, 8, 31),
    ]
    assert windows[-1]["overlap_start"] == date(2026, 8, 29)
    assert windows[-1]["number_of_days"] == 3
    assert sum(w["number_of_days"] for w in windows) == 31


def test_week_ending_for_period_assigns_cross_month_week_once():
    # Mon Aug 31 - Sun Sep 6 is mostly September -> week ending Fri Sep 4.
    assert _week_ending_for_period(date(2026, 8, 31), date(2026, 9, 6), FRIDAY) == date(2026, 9, 4)
    assert _week_ending_for_period(date(2026, 9, 14), date(2026, 9, 20), FRIDAY) == date(2026, 9, 18)


@pytest.mark.asyncio
async def test_hcp_weekly_labor_totals_installer():
    async with await _seed_db() as db:
        weekly = await _hcp_weekly_labor_totals(db, "install", 2026, FRIDAY)

        assert set(weekly) == {"2026-08-28", "2026-09-11", "2026-09-18"}

        totals = weekly["2026-09-18"]
        assert totals["snapshot_id"] == 3
        assert totals["period_start"] == "2026-09-14"
        assert totals["period_end"] == "2026-09-20"
        assert totals["head_count"] == 2
        assert totals["regular_hours"] == round(24.21 + 40.0 + 10.0 + 0.0 + 19.5 + 40.0, 2)
        assert totals["overtime_hours"] == round(17.43 + 0.0 + 16.24, 2)
        assert totals["wages_basic"] == round(968.4 + 100.0 + 475.02, 2)
        assert totals["overtime_wages"] == round(17.43 + 0.0 + 16.24, 2)
        assert totals["total_labor_cost"] == round(totals["wages_basic"] + totals["overtime_wages"], 2)
        assert totals["total_hours"] == round(totals["regular_hours"] + totals["overtime_hours"], 2)

        assert weekly["2026-09-11"]["snapshot_id"] == 1
        assert weekly["2026-09-11"]["total_labor_cost"] == round(1180.0 + 442.5, 2)

        assert weekly["2026-08-28"]["snapshot_id"] == 4
        assert weekly["2026-08-28"]["period_start"] == "2026-08-24"
        assert weekly["2026-08-28"]["wages_basic"] == 1600.0


@pytest.mark.asyncio
async def test_hcp_weekly_labor_totals_fabrication():
    async with await _seed_db() as db:
        weekly = await _hcp_weekly_labor_totals(db, "fabrication", 2026, FRIDAY)

        totals = weekly["2026-09-18"]
        assert totals["snapshot_id"] == 3
        assert totals["head_count"] == 1
        assert totals["regular_hours"] == round(18.0 + 40.0, 2)
        assert totals["overtime_hours"] == 9.96
        assert totals["wages_basic"] == 720.0
        assert totals["overtime_wages"] == 9.96
        # Weeks whose pull has no Fabrication rows still resolve to zero totals.
        assert weekly["2026-09-11"]["total_labor_cost"] == 0.0


@pytest.mark.asyncio
async def test_hcp_weekly_labor_totals_returns_empty_without_snapshots():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await _create_tables(connection)

    async with AsyncSession(engine, expire_on_commit=False) as db:
        assert await _hcp_weekly_labor_totals(db, "install", 2026, FRIDAY) == {}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("month", "expected"),
    [
        (8, None),  # No roster pull covers August or earlier.
        (9, 39),  # Most recent pull covering a September week.
        (10, 50),
        (12, 50),  # No December pull yet -> most recent earlier pull.
    ],
)
async def test_hcp_active_employee_count_for_month(month, expected):
    async with await _seed_db() as db:
        assert await _hcp_active_employee_count_for_month(db, 2026, month) == expected


def _week_row(week_key: str, **values) -> dict:
    row = {key: 0.0 for key in _INSTALLER_METRIC_KEYS}
    row.update({"week_ending": week_key, "has_data": True, "number_of_days_per_week": 7}, **values)
    return row


def test_installer_period_totals_sums_data_weeks_and_ignores_blank_weeks():
    rows = [
        _week_row("2026-09-04", total_head_count=10.0, wages_basic_installer=1000.0, overtime_installer=100.0,
                  total_labor_cost=1100.0, regular_hours=40.0, overtime_hours=5.0, total_hours=45.0,
                  completed_sqft_per_week=100.0, gross_revenue=5000.0, overhead_per_week=500.0),
        # Week without an HCP pull: head count 0 must not drag the average down.
        _week_row("2026-09-11", completed_sqft_per_week=50.0, gross_revenue=2500.0, overhead_per_week=500.0),
        _blank_installer_week_row("2026-10-02"),
    ]

    totals = _installer_period_totals(rows)

    assert totals["number_of_weeks"] == 3
    assert totals["weeks_with_data"] == 2
    assert totals["has_data"] is True
    assert totals["number_of_days_per_week"] == 14
    assert totals["total_head_count"] == 10.0
    assert totals["total_labor_cost"] == 1100.0
    assert totals["completed_sqft_per_week"] == 150.0
    assert totals["overhead_per_week"] == 1000.0
    assert totals["overtime_pct"] == 10.0
    assert totals["labor_cost_pct_per_dollar_sold"] == round(1100.0 / 7500.0 * 100, 2)
    assert set(_INSTALLER_METRIC_KEYS) <= set(totals)


def test_installer_period_totals_is_blank_without_data():
    totals = _installer_period_totals([_blank_installer_week_row("2026-12-04")])

    assert totals["has_data"] is False
    assert totals["weeks_with_data"] == 0
    assert all(totals[key] is None for key in _INSTALLER_METRIC_KEYS)


class _FrozenDate(date):
    @classmethod
    def today(cls):
        return cls(2026, 9, 25)


class _EmptyResult:
    def first(self):
        return (None, None, None)


class _EmptyDb:
    async def execute(self, *_args, **_kwargs):
        return _EmptyResult()


@pytest.mark.asyncio
async def test_installer_report_blanks_future_weeks_and_builds_annual_months(monkeypatch):
    import json

    from src.app.routers import reports

    hcp_week = {
        "head_count": 10, "wages_basic": 9737.75, "overtime_wages": 5296.86, "total_labor_cost": 15034.61,
        "regular_hours": 376.04, "overtime_hours": 139.48, "total_hours": 515.52, "snapshot_id": 1,
        "period_start": "2026-09-14", "period_end": "2026-09-20", "pulled_at": "2026-09-25T11:27:42",
    }

    async def _weekly(*_args, **_kwargs):
        return {"2026-09-18": hcp_week}

    async def _roster(*_args, **_kwargs):
        return 40

    monkeypatch.setattr(reports, "date", _FrozenDate)
    monkeypatch.setattr(reports, "_hcp_weekly_labor_totals", _weekly)
    monkeypatch.setattr(reports, "_hcp_active_employee_count_for_month", _roster)

    response = await reports.get_owner_weekly_installer_labor_cost_report(
        year=2026, month=9, total_employees=None, overhead_per_week=18512.69, week_ending_weekday=FRIDAY,
        payroll_overrides_json=None, db=_EmptyDb(), current_user=None,
    )
    data = json.loads(response.body)["data"]

    weeks = {row["week_ending"]: row for row in data["monthly_report"]["weekly_breakdown"]}
    assert list(weeks) == ["2026-09-04", "2026-09-11", "2026-09-18", "2026-09-25", "2026-09-30"]
    assert weeks["2026-09-18"]["total_labor_cost"] == 15034.61
    assert weeks["2026-09-18"]["hcp_payroll_snapshot_id"] == 1
    assert weeks["2026-09-11"]["total_labor_cost"] == 0.0  # Started week, no HCP pull.
    assert weeks["2026-09-30"]["has_data"] is False  # Sep 26-30 hasn't started.
    assert weeks["2026-09-30"]["total_labor_cost"] is None

    annual = data["annual_report"]
    months = {row["month_number"]: row for row in annual["monthly_breakdown"]}
    assert len(months) == 12
    assert months[9]["total_labor_cost"] == 15034.61
    assert months[9]["weeks_with_data"] == 4
    assert months[10]["has_data"] is False
    assert months[10]["total_labor_cost"] is None
    assert data["monthly_report"]["totals"] == {k: v for k, v in months[9].items() if k not in ("month", "month_number")}
    # The year row is the sum of every week with data across all months.
    assert annual["totals"]["total_labor_cost"] == 15034.61
    assert annual["totals"]["weeks_with_data"] == sum(m["weeks_with_data"] for m in months.values())
    assert data["annual_monthly_summary"][9]["total_labor_cost"] is None
