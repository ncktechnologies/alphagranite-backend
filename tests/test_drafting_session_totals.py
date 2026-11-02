from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.app.interface.business_schemas import DraftingSessionAction
from src.app.routers import drafting


def make_db(session):
    """Every query in the handler gets the same result: a truthy fab/drafter,
    the active session, and no notes."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = object()
    result.scalars.return_value.first.return_value = session
    result.scalars.return_value.all.return_value = []
    return SimpleNamespace(
        execute=AsyncMock(return_value=result),
        add=MagicMock(), flush=AsyncMock(), commit=AsyncMock(), refresh=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_repeated_pauses_report_actual_work_time():
    # FAB 16123's real event history: 23:09 + 1:20:51 + 0:16 + 0:22 of work.
    session = SimpleNamespace(
        id=1062, fab_id=16123, drafter_id=7, status="drafting",
        session_start_time=datetime(2026, 10, 26, 7, 36, 44),
        total_time_spent=0, total_pause_duration=0, current_pause_start_time=None,
        cumulative_sqft_drafted="0", work_percentage_done=0, updated_at=None,
    )
    db = make_db(session)
    admin = SimpleNamespace(is_super_admin=True)
    events = [
        ("pause", datetime(2026, 10, 26, 7, 59, 53)),
        ("resume", datetime(2026, 10, 27, 6, 9, 17)),
        ("pause", datetime(2026, 10, 27, 7, 30, 8)),
        ("resume", datetime(2026, 10, 27, 7, 30, 15)),
        ("pause", datetime(2026, 10, 27, 7, 30, 31)),
        ("resume", datetime(2026, 10, 27, 7, 30, 43)),
        ("pause", datetime(2026, 10, 27, 7, 31, 5)),
    ]
    for action, ts in events:
        await drafting.manage_drafting_session(
            16123, DraftingSessionAction(drafter_id=7, action=action, timestamp=ts), db, admin
        )

    assert session.status == "paused"
    assert session.total_time_spent == 1 * 3600 + 44 * 60 + 38  # 1:44:38, not 5:36:03
