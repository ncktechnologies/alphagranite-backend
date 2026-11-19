from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app.database.status import Status
from src.app.database.stone_color import StoneColor
from src.app.database.stone_type import StoneType
from src.app.interface.business_schemas import StoneColorUpdate, StoneTypeUpdate
from src.app.routers import stone_colors, stone_types

USER = SimpleNamespace(id=1)


@pytest.fixture
def session(monkeypatch):
    engine = create_engine("sqlite://")
    for table in (Status.__table__, StoneType.__table__, StoneColor.__table__):
        table.create(engine)
    with Session(engine) as db_session:
        # Inactive's primary key differs from its value_id, like "On Hold" (id 9, value_id 0) in production.
        db_session.add_all([
            Status(id=1, name="Active", slug="active", value_id=1),
            Status(id=12, name="Inactive", slug="inactive", value_id=2),
        ])
        db_session.add_all([
            StoneType(id=1, name="Granite", status_id=1, created_by=1),
            StoneType(id=2, name="Marble", status_id=2, created_by=1),
            StoneType(id=3, name="Quartz", status_id=1, created_by=1),
        ])
        db_session.add_all([
            StoneColor(id=1, stone_type_id=1, name="Black Pearl", status_id=1, created_by=1),
            StoneColor(id=2, stone_type_id=1, name="Absolute Black", status_id=2, created_by=1),
            StoneColor(id=3, stone_type_id=3, name="Calacatta", status_id=1, created_by=1),
        ])
        db_session.commit()
        for router in (stone_types, stone_colors):
            monkeypatch.setattr(router, "success_response", lambda data, message: data)
        yield db_session
    engine.dispose()


def as_async_db(db_session):
    return SimpleNamespace(
        execute=AsyncMock(side_effect=db_session.execute),
        get=AsyncMock(side_effect=db_session.get),
        commit=AsyncMock(side_effect=db_session.commit),
        refresh=AsyncMock(side_effect=db_session.refresh),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("status_id, expected", [(None, [1, 2, 3]), (1, [1, 3]), (2, [2])])
async def test_stone_type_list_filters_by_status(session, status_id, expected):
    result = await stone_types.get_stone_types(
        skip=0, limit=100, status_id=status_id, search=None, db=as_async_db(session), current_user=USER,
    )
    assert [stone_type.id for stone_type in result] == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("status_id, expected", [(None, [2, 1, 3]), (1, [1, 3]), (2, [2])])
async def test_stone_color_list_filters_by_status(session, status_id, expected):
    result = await stone_colors.get_stone_colors(
        skip=0, limit=100, stone_type_id=None, status_id=status_id, search=None,
        db=as_async_db(session), current_user=USER,
    )
    assert [color.id for color in result] == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("status_id, expected", [(None, [2, 1]), (1, [1]), (2, [2])])
async def test_stone_colors_by_type_filters_by_status(session, status_id, expected):
    result = await stone_colors.get_stone_colors_by_type(
        stone_type_id=1, status_id=status_id, db=as_async_db(session), current_user=USER,
    )
    assert [color.id for color in result] == expected


@pytest.mark.asyncio
async def test_stone_type_can_be_toggled_inactive_and_back(session):
    db = as_async_db(session)
    result = await stone_types.update_stone_type(
        type_id=1, stone_type_data=StoneTypeUpdate(status_id=2), db=db, current_user=USER,
    )
    assert result.status_id == 2

    result = await stone_types.update_stone_type(
        type_id=1, stone_type_data=StoneTypeUpdate(status_id=1), db=db, current_user=USER,
    )
    assert result.status_id == 1


@pytest.mark.asyncio
async def test_stone_color_can_be_toggled_inactive(session):
    result = await stone_colors.update_stone_color(
        color_id=1, color_data=StoneColorUpdate(status_id=2), db=as_async_db(session), current_user=USER,
    )
    assert result.status_id == 2


@pytest.mark.asyncio
async def test_stone_status_update_rejects_unknown_status(session):
    with pytest.raises(Exception) as error:
        await stone_types.update_stone_type(
            type_id=1, stone_type_data=StoneTypeUpdate(status_id=12), db=as_async_db(session), current_user=USER,
        )
    assert getattr(error.value, "status_code", None) == 400
    assert session.get(StoneType, 1).status_id == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("params, expected_total, expected_ids, expected_page", [
    (dict(skip=0, limit=2), 3, [2, 1], 1),
    (dict(skip=2, limit=2), 3, [3], 2),
    (dict(skip=0, limit=50, search=" black "), 2, [2, 1], 1),
    (dict(skip=0, limit=50, search="BLACK", status_id=1), 1, [1], 1),
    (dict(skip=0, limit=50, stone_type_id=1, status_id=2), 1, [2], 1),
    (dict(skip=0, limit=50, search="no such color"), 0, [], 1),
])
async def test_stone_colors_paginated_returns_page_and_total(
    session, params, expected_total, expected_ids, expected_page,
):
    kwargs = dict(stone_type_id=None, status_id=None, search=None)
    kwargs.update(params)
    result = await stone_colors.get_stone_colors_paginated(**kwargs, db=as_async_db(session), current_user=USER)

    assert result["total"] == expected_total
    assert [color.id for color in result["data"]] == expected_ids
    assert result["page"] == expected_page
    assert result["per_page"] == params["limit"]


def test_paginated_route_is_matched_before_color_id_route():
    paths = [route.path for route in stone_colors.router.routes]
    assert paths.index("/stone-colors/paginated") < paths.index("/stone-colors/{color_id}")
