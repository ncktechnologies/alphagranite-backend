from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app.database.stone_thickness import StoneThickness
from src.app.routers import stone_thickness


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_id, skip, limit, expected_ids",
    [
        (None, 0, 100, [2, 3, 4]),
        (0, 0, 100, []),
        (1, 0, 100, [2, 4]),
        (2, 0, 100, [3]),
        (None, 1, 1, [3]),
    ],
)
async def test_list_hides_status_zero_before_pagination(monkeypatch, status_id, skip, limit, expected_ids):
    engine = create_engine("sqlite://")
    try:
        StoneThickness.__table__.create(engine)
        with Session(engine) as session:
            for thickness_id, status, millimeters in [(1, 0, 50), (2, 1, 30), (3, 2, 20), (4, 1, 10)]:
                session.add(StoneThickness(
                    id=thickness_id,
                    thickness=f"Thickness {thickness_id}",
                    thickness_mm=millimeters,
                    status_id=status,
                    created_by=1,
                ))
            session.commit()
            db = SimpleNamespace(execute=AsyncMock(side_effect=session.execute))
            monkeypatch.setattr(stone_thickness, "success_response", lambda data, message: data)

            result = await stone_thickness.get_stone_thicknesses(
                skip=skip, limit=limit, status_id=status_id, db=db, current_user=SimpleNamespace(id=1),
            )

            assert [thickness.id for thickness in result] == expected_ids
    finally:
        engine.dispose()