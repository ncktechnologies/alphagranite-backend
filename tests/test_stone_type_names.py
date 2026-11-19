from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine

from src.app.database.stone_type import StoneType
from src.app.routers.stone_types import _stone_type_name_taken


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    StoneType.__table__.create(engine)
    with engine.begin() as conn:
        conn.execute(StoneType.__table__.insert(), [{"id": 1, "name": "Quartz", "status_id": 1, "created_by": 1}])
        yield SimpleNamespace(execute=AsyncMock(side_effect=conn.execute))
    engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["Quartz", "quartz", "QUARTZ", "  quartz "])
async def test_duplicate_names_ignore_case_and_spaces(db, name):
    assert await _stone_type_name_taken(db, name)


@pytest.mark.asyncio
async def test_new_name_and_renaming_itself_are_allowed(db):
    assert not await _stone_type_name_taken(db, "Granite")
    assert not await _stone_type_name_taken(db, "QUARTZ", exclude_id=1)
