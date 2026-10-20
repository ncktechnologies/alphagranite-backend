from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app.database.edge import Edge
from src.app.routers import edges


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_id, search, skip, limit, expected_ids",
    [
        (None, None, 0, 100, [2, 3, 4]),
        (0, None, 0, 100, []),
        (1, None, 0, 100, [2, 4]),
        (2, None, 0, 100, [3]),
        (None, None, 1, 1, [3]),
        (None, "miter", 0, 100, [2]),
    ],
)
async def test_list_hides_status_zero_before_pagination(monkeypatch, status_id, search, skip, limit, expected_ids):
    engine = create_engine("sqlite://")
    try:
        Edge.__table__.create(engine)
        with Session(engine) as session:
            for edge_id, status, name in [(1, 0, "A MITER"), (2, 1, "B MITER"), (3, 2, "C BEVEL"), (4, 1, "D OGEE")]:
                session.add(Edge(id=edge_id, name=name, edge_type="Standard", status_id=status, created_by=1))
            session.commit()
            db = SimpleNamespace(execute=AsyncMock(side_effect=session.execute))
            monkeypatch.setattr(edges, "success_response", lambda data, message: data)

            result = await edges.get_edges(
                skip=skip, limit=limit, status_id=status_id, edge_type=None, search=search,
                db=db, current_user=SimpleNamespace(id=1),
            )

            assert [edge.id for edge in result] == expected_ids
    finally:
        engine.dispose()
