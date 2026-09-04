"""
Focused unit tests for installer job timer validation added to prevent:
1. An installer from running more than one job timer at a time (across ANY job/fab).
2. Stopping a lead installer's timer without providing sqft_installed/sqft_not_installed.
"""
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest
from fastapi import HTTPException

from src.app.routers.job_timers import (
    INSTALLER_ROLE_EXTRA_CREW,
    INSTALLER_ROLE_LEAD,
    _enforce_required_sqft_on_stop,
    start_installer_job_timer,
    stop_installer_job_timer,
)
from src.app.interface.business_schemas import InstallerJobTimerCommandRequest


class TestEnforceRequiredSqftOnStop:
    def test_lead_missing_sqft_installed_raises(self):
        payload = InstallerJobTimerCommandRequest(sqft_installed=None, sqft_not_installed=10)
        with pytest.raises(HTTPException) as exc_info:
            _enforce_required_sqft_on_stop(payload, INSTALLER_ROLE_LEAD)
        assert exc_info.value.status_code == 400

    def test_lead_missing_sqft_not_installed_raises(self):
        payload = InstallerJobTimerCommandRequest(sqft_installed=10, sqft_not_installed=None)
        with pytest.raises(HTTPException) as exc_info:
            _enforce_required_sqft_on_stop(payload, INSTALLER_ROLE_LEAD)
        assert exc_info.value.status_code == 400

    def test_lead_no_payload_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            _enforce_required_sqft_on_stop(None, INSTALLER_ROLE_LEAD)
        assert exc_info.value.status_code == 400

    def test_lead_with_both_fields_passes(self):
        payload = InstallerJobTimerCommandRequest(sqft_installed=10, sqft_not_installed=5)
        _enforce_required_sqft_on_stop(payload, INSTALLER_ROLE_LEAD)  # should not raise

    def test_extra_crew_no_payload_passes(self):
        _enforce_required_sqft_on_stop(None, INSTALLER_ROLE_EXTRA_CREW)  # should not raise


@pytest.mark.asyncio
class TestStartInstallerJobTimerConflict:
    async def test_blocks_when_installer_has_running_timer_on_another_job(self):
        db = AsyncMock()
        job_result = Mock()
        job_result.scalar_one_or_none.return_value = SimpleNamespace(id=75)

        conflict_job = SimpleNamespace(id=41, job_number="41")
        conflict_session = SimpleNamespace(fab_id=None)
        conflict_result = Mock()
        conflict_result.first.return_value = (conflict_session, conflict_job)

        db.execute.side_effect = [job_result, conflict_result]
        current_user = SimpleNamespace(id=9)

        with pytest.raises(HTTPException) as exc_info:
            await start_installer_job_timer(
                job_id=75,
                payload=None,
                fab_id=None,
                db=db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == 409
        assert "Job #41" in exc_info.value.detail

    async def test_succeeds_when_no_conflicting_timer_exists(self):
        db = AsyncMock()
        job_result = Mock()
        job_result.scalar_one_or_none.return_value = SimpleNamespace(id=75)

        conflict_result = Mock()
        conflict_result.first.return_value = None

        db.execute.side_effect = [job_result, conflict_result]
        current_user = SimpleNamespace(id=9)

        response = await start_installer_job_timer(
            job_id=75,
            payload=None,
            fab_id=None,
            db=db,
            current_user=current_user,
        )

        assert response["success"] is True
        assert response["data"]["job_id"] == 75
        assert response["data"]["installer_id"] == 9
        assert response["data"]["status"] == "running"


@pytest.mark.asyncio
class TestStopInstallerJobTimerRequiresSqft:
    async def test_lead_stop_without_sqft_raises_400(self):
        db = AsyncMock()
        session = SimpleNamespace(
            id=1,
            job_id=75,
            fab_id=None,
            installer_id=9,
            installer_role=INSTALLER_ROLE_LEAD,
            status="running",
            current_run_start_at=None,
            current_pause_start_at=None,
            sqft_installed=None,
            sqft_not_installed=None,
        )
        stop_result = Mock()
        stop_result.scalar_one_or_none.return_value = session
        scheduling_result = Mock()
        scheduling_result.scalar_one_or_none.return_value = SimpleNamespace(
            installer_id=9, extra_crew_1_id=None, extra_crew_2_id=None, extra_crew_3_id=None
        )
        db.execute.side_effect = [stop_result, scheduling_result]
        current_user = SimpleNamespace(id=9)

        with pytest.raises(HTTPException) as exc_info:
            await stop_installer_job_timer(
                job_id=75,
                payload=None,
                fab_id=None,
                db=db,
                current_user=current_user,
            )

        assert exc_info.value.status_code == 400

    async def test_lead_stop_with_sqft_succeeds(self):
        db = AsyncMock()
        session = SimpleNamespace(
            id=1,
            job_id=75,
            fab_id=None,
            installer_id=9,
            installer_role=INSTALLER_ROLE_LEAD,
            status="running",
            current_run_start_at=None,
            current_pause_start_at=None,
            sqft_installed=None,
            sqft_not_installed=None,
            stopped_at=None,
            total_work_seconds=0,
            total_pause_seconds=0,
            session_start_at=None,
        )
        stop_result = Mock()
        stop_result.scalar_one_or_none.return_value = session
        scheduling_result = Mock()
        scheduling_result.scalar_one_or_none.return_value = SimpleNamespace(
            installer_id=9, extra_crew_1_id=None, extra_crew_2_id=None, extra_crew_3_id=None
        )
        db.execute.side_effect = [stop_result, scheduling_result]
        current_user = SimpleNamespace(id=9)
        payload = InstallerJobTimerCommandRequest(sqft_installed=12.5, sqft_not_installed=0)

        response = await stop_installer_job_timer(
            job_id=75,
            payload=payload,
            fab_id=None,
            db=db,
            current_user=current_user,
        )

        assert response["success"] is True
        assert response["data"]["sqft_installed"] == 12.5
        assert response["data"]["sqft_not_installed"] == 0

    async def test_extra_crew_stop_without_sqft_succeeds(self):
        db = AsyncMock()
        session = SimpleNamespace(
            id=2,
            job_id=75,
            fab_id=None,
            installer_id=10,
            installer_role=INSTALLER_ROLE_EXTRA_CREW,
            status="running",
            current_run_start_at=None,
            current_pause_start_at=None,
            sqft_installed=None,
            sqft_not_installed=None,
            stopped_at=None,
            total_work_seconds=0,
            total_pause_seconds=0,
            session_start_at=None,
        )
        stop_result = Mock()
        stop_result.scalar_one_or_none.return_value = session
        scheduling_result = Mock()
        scheduling_result.scalar_one_or_none.return_value = SimpleNamespace(
            installer_id=9, extra_crew_1_id=10, extra_crew_2_id=None, extra_crew_3_id=None
        )
        db.execute.side_effect = [stop_result, scheduling_result]
        current_user = SimpleNamespace(id=10)

        response = await stop_installer_job_timer(
            job_id=75,
            payload=None,
            fab_id=None,
            db=db,
            current_user=current_user,
        )

        assert response["success"] is True
        assert response["data"]["status"] == "stopped"
