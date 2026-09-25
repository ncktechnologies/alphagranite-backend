import os
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

os.environ.setdefault("SECRET_KEY", "testsecretkey")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

pytest.importorskip("aiosqlite")

from src.app.routers.reports import _hcp_cost_center_labor_totals, _latest_active_employee_count


async def _seed_db() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
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
                created_at DATETIME NOT NULL
            )
        """))
        await connection.execute(text("""
            CREATE TABLE hcp_staff_roster_snapshots (
                id INTEGER PRIMARY KEY,
                source_config_id INTEGER NOT NULL,
                ingestion_run_id INTEGER NOT NULL,
                report_settings_id VARCHAR(100) NOT NULL,
                pulled_at DATETIME NOT NULL,
                active_employee_count INTEGER NOT NULL
            )
        """))

        await connection.execute(text("""
            INSERT INTO users (id, username, hcp_employee_id) VALUES (1, 'jhernandez', '247')
        """))

        # Older snapshot -- must be ignored in favor of the newest one.
        await connection.execute(text("""
            INSERT INTO hcp_payroll_report_snapshots (id, source_config_id, ingestion_run_id, report_settings_id, created_at)
            VALUES (1, 1, 1, '89798180', '2026-01-01 00:00:00')
        """))
        await connection.execute(text("""
            INSERT INTO hcp_payroll_report_rows
                (id, snapshot_id, source_config_id, ingestion_run_id, row_kind, row_index, cost_center_name,
                 employee_id, employee_first_name, employee_last_name, regular_hours, holiday_hours,
                 overtime_hours, total_reg_pto_hol_wages, total_ot_wages, created_at)
            VALUES
                (1, 1, 1, 1, 'detail', 1, 'Install-Old', '999', 'Old', 'Guy', 1, 0, 0, 1, 0, '2026-01-01 00:00:00')
        """))

        # Newest snapshot -- this is the one that should be used.
        await connection.execute(text("""
            INSERT INTO hcp_payroll_report_snapshots (id, source_config_id, ingestion_run_id, report_settings_id, created_at)
            VALUES (2, 1, 1, '89798180', '2026-09-20 00:00:00')
        """))
        await connection.execute(
            text("""
                INSERT INTO hcp_payroll_report_rows
                    (id, snapshot_id, source_config_id, ingestion_run_id, row_kind, row_index, cost_center_name,
                     employee_id, employee_first_name, employee_last_name, regular_hours, holiday_hours,
                     overtime_hours, total_reg_pto_hol_wages, total_ot_wages, created_at)
                VALUES
                    -- Employee 247 split across two Install cost centers -> must combine into one head.
                    (2, 2, 1, 1, 'detail', 1, 'Install-Omar', '247', 'Jose', 'Hernandez', 24.21, 40.0, 17.43, 968.4, 17.43, '2026-09-20 00:00:00'),
                    (3, 2, 1, 1, 'detail', 2, 'Install Tony', '247', 'Jose', 'Hernandez', 10.0, 0.0, 0.0, 100.0, 0.0, '2026-09-20 00:00:00'),
                    -- Legacy row without employee_id -> dedup falls back to name.
                    (4, 2, 1, 1, 'detail', 3, 'Install-General', NULL, 'Roger', 'Olivo', 19.5, 40.0, 16.24, 475.02, 16.24, '2026-09-20 00:00:00'),
                    -- Fabrication row -- must not be counted in Install totals.
                    (5, 2, 1, 1, 'detail', 4, 'Fabrication', '54', 'Jose', 'Corona', 18.0, 40.0, 9.96, 720.0, 9.96, '2026-09-20 00:00:00'),
                    -- Subtotal row -- must be excluded from all totals.
                    (6, 2, 1, 1, 'subtotal', 5, 'Install-General', NULL, NULL, NULL, 999, NULL, 999, 999, 999, '2026-09-20 00:00:00')
            """)
        )

        # Two roster snapshots -- must use the most recent one's active_employee_count.
        await connection.execute(text("""
            INSERT INTO hcp_staff_roster_snapshots (id, source_config_id, ingestion_run_id, report_settings_id, pulled_at, active_employee_count)
            VALUES
                (1, 1, 1, '93428419', '2026-09-01 00:00:00', 5),
                (2, 1, 1, '93428419', '2026-09-20 00:00:00', 39)
        """))

    return AsyncSession(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_hcp_cost_center_labor_totals_installer():
    async with await _seed_db() as db:
        totals = await _hcp_cost_center_labor_totals(db, "install")

        assert totals["snapshot_id"] == 2
        assert totals["head_count"] == 2
        assert totals["regular_hours"] == round(24.21 + 40.0 + 10.0 + 0.0 + 19.5 + 40.0, 2)
        assert totals["overtime_hours"] == round(17.43 + 0.0 + 16.24, 2)
        assert totals["wages_basic"] == round(968.4 + 100.0 + 475.02, 2)
        assert totals["overtime_wages"] == round(17.43 + 0.0 + 16.24, 2)
        assert totals["total_labor_cost"] == round(totals["wages_basic"] + totals["overtime_wages"], 2)
        assert totals["total_hours"] == round(totals["regular_hours"] + totals["overtime_hours"], 2)


@pytest.mark.asyncio
async def test_hcp_cost_center_labor_totals_fabrication():
    async with await _seed_db() as db:
        totals = await _hcp_cost_center_labor_totals(db, "fabrication")

        assert totals["snapshot_id"] == 2
        assert totals["head_count"] == 1
        assert totals["regular_hours"] == round(18.0 + 40.0, 2)
        assert totals["overtime_hours"] == 9.96
        assert totals["wages_basic"] == 720.0
        assert totals["overtime_wages"] == 9.96


@pytest.mark.asyncio
async def test_hcp_cost_center_labor_totals_returns_empty_without_snapshots():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.execute(text("""
            CREATE TABLE hcp_payroll_report_snapshots (
                id INTEGER PRIMARY KEY, source_config_id INTEGER NOT NULL,
                ingestion_run_id INTEGER NOT NULL, report_settings_id VARCHAR(100) NOT NULL,
                created_at DATETIME NOT NULL
            )
        """))
        await connection.execute(text("""
            CREATE TABLE hcp_payroll_report_rows (
                id INTEGER PRIMARY KEY, snapshot_id INTEGER NOT NULL, source_config_id INTEGER NOT NULL,
                ingestion_run_id INTEGER NOT NULL, row_kind VARCHAR(50) NOT NULL, row_index INTEGER NOT NULL,
                cost_center_name VARCHAR(255), employee_id VARCHAR(100), employee_first_name VARCHAR(255),
                employee_last_name VARCHAR(255), hourly_pay FLOAT, regular_hours FLOAT, holiday_hours FLOAT,
                pto_hours FLOAT, total_reg_pto_hol_wages FLOAT, overtime_hours FLOAT, total_ot_wages FLOAT,
                raw_line_text VARCHAR
            )
        """))
        await connection.execute(text("""
            CREATE TABLE users (id INTEGER PRIMARY KEY, username VARCHAR(255), hcp_employee_id VARCHAR(255))
        """))

    async with AsyncSession(engine, expire_on_commit=False) as db:
        totals = await _hcp_cost_center_labor_totals(db, "install")
        assert totals["snapshot_id"] is None
        assert totals["head_count"] == 0
        assert totals["total_labor_cost"] == 0.0


@pytest.mark.asyncio
async def test_latest_active_employee_count_uses_most_recent_roster_snapshot():
    async with await _seed_db() as db:
        active_count = await _latest_active_employee_count(db)
        assert active_count == 39
