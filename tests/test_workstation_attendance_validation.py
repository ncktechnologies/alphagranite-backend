import os
from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

os.environ.setdefault("SECRET_KEY", "testsecretkey")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

pytest.importorskip("aiosqlite")

from src.app.routers.shop_cut_plan import _assert_no_shop_plan_conflicts
from src.app.routers.workstation import WorkstationCreate, _serialize_workstation


def test_workstation_create_defaults_attendance_required_to_false():
    payload = WorkstationCreate(name="Saw 1", status_id=1)
    workstation = SimpleNamespace(
        id=1,
        name=payload.name,
        is_active=payload.is_active,
        attendance_required=payload.attendance_required,
        status_id=payload.status_id,
        planning_section_id=None,
        operator_ids=[],
        created_at=datetime(2026, 9, 4, 8, 0),
        created_by=1,
        updated_at=None,
        updated_by=None,
    )

    response = _serialize_workstation(workstation)

    assert payload.attendance_required is False
    assert response["attendance_required"] is False


async def _create_attendance_test_session(
    existing_attendance_required: bool,
    new_attendance_required: bool,
) -> tuple[AsyncSession, object]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.execute(text("""
            CREATE TABLE work_stations (
                id INTEGER PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                is_active BOOLEAN NOT NULL,
                attendance_required BOOLEAN NOT NULL,
                status_id INTEGER NOT NULL,
                planning_section_id INTEGER,
                operator_ids JSON,
                created_at DATETIME NOT NULL,
                created_by INTEGER NOT NULL,
                updated_at DATETIME,
                updated_by INTEGER
            )
        """))
        await connection.execute(text("""
            CREATE TABLE shop_cut_plans (
                id INTEGER PRIMARY KEY,
                fab_id INTEGER NOT NULL,
                workstation_id INTEGER NOT NULL,
                planning_section_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                sequence INTEGER NOT NULL,
                estimated_hours FLOAT NOT NULL,
                scheduled_start_date DATETIME,
                scheduled_end_date DATETIME,
                actual_start_date DATETIME,
                actual_end_date DATETIME,
                work_percentage INTEGER NOT NULL,
                notes VARCHAR,
                created_at DATETIME NOT NULL,
                created_by INTEGER NOT NULL,
                updated_at DATETIME,
                updated_by INTEGER
            )
        """))
        await connection.execute(
            text("""
                INSERT INTO work_stations
                    (id, name, is_active, attendance_required, status_id, created_at, created_by)
                VALUES
                    (10, 'Existing WS', 1, :existing_required, 1, '2026-09-04 08:00:00', 1),
                    (20, 'New WS', 1, :new_required, 1, '2026-09-04 08:00:00', 1)
            """),
            {
                "existing_required": existing_attendance_required,
                "new_required": new_attendance_required,
            },
        )
        await connection.execute(text("""
            INSERT INTO shop_cut_plans
                (id, fab_id, workstation_id, planning_section_id, user_id, sequence,
                 estimated_hours, scheduled_start_date, scheduled_end_date,
                 work_percentage, created_at, created_by)
            VALUES
                (1, 1, 10, 1, 7, 1, 2.0, '2026-09-04 09:00:00',
                 '2026-09-04 11:00:00', 0, '2026-09-04 08:00:00', 1)
        """))

    return AsyncSession(engine, expire_on_commit=False), engine


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("existing_required", "new_required", "expected_workstation"),
    [
        (True, False, "Existing WS"),
        (False, True, "New WS"),
        (True, True, "Existing WS"),
    ],
)
async def test_overlapping_plan_fails_when_attendance_is_required(
    existing_required: bool,
    new_required: bool,
    expected_workstation: str,
):
    session, engine = await _create_attendance_test_session(existing_required, new_required)
    async with session:
        with pytest.raises(HTTPException) as exc_info:
            await _assert_no_shop_plan_conflicts(
                session,
                plan_id=0,
                fab_id=2,
                workstation_id=20,
                operator_id=7,
                scheduled_start=datetime(2026, 9, 4, 10, 0),
                estimated_hours=1,
            )

    await engine.dispose()
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        f"Cannot assign plan: Attendance is required for workstation {expected_workstation}."
    )


@pytest.mark.asyncio
async def test_overlapping_plan_succeeds_when_attendance_is_not_required():
    session, engine = await _create_attendance_test_session(False, False)
    async with session:
        await _assert_no_shop_plan_conflicts(
            session,
            plan_id=0,
            fab_id=2,
            workstation_id=20,
            operator_id=7,
            scheduled_start=datetime(2026, 9, 4, 10, 0),
            estimated_hours=1,
        )
    await engine.dispose()


@pytest.mark.asyncio
async def test_non_overlapping_plan_succeeds_when_attendance_is_required():
    session, engine = await _create_attendance_test_session(True, True)
    async with session:
        await _assert_no_shop_plan_conflicts(
            session,
            plan_id=0,
            fab_id=2,
            workstation_id=20,
            operator_id=7,
            scheduled_start=datetime(2026, 9, 4, 12, 0),
            estimated_hours=1,
        )
    await engine.dispose()
