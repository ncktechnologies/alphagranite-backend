import inspect
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, MetaData, String, Table, create_engine, func, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import visitors
from sqlalchemy.sql.selectable import Subquery

from src.app.database.business_job import BusinessJob
from src.app.database.fab import Fab
from src.app.database.templating import Templating
from src.app.routers import fabs


def compile_sql(query):
    return str(query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True},
    ))


def latest_templating():
    return (
        select(Templating).where(Templating.fab_id == Fab.id)
        .order_by(Templating.id.desc()).limit(1).lateral("latest_templating")
    )


@pytest.mark.parametrize("stage", [None, "drafting", "templating", "install_completion"])
def test_pagination_limits_ids_before_detail_joins(stage):
    latest = latest_templating()
    query = fabs._build_fab_list_query(
        None, None, None, None, stage, None, None, None, latest,
    )
    paginated = fabs._paginate_fab_list_query(query, 25, 25, stage, latest)
    sql = compile_sql(paginated)
    page_sql = sql.split("FROM (SELECT fabs.id AS id", 1)[1].split(") AS fab_page", 1)[0]

    assert "LIMIT 25 OFFSET 25" in page_sql
    assert "JOIN users" not in page_sql
    assert "JOIN stone_types" not in page_sql
    assert "JOIN business_jobs" not in page_sql
    assert "LATERAL" in page_sql if stage == "templating" else "LATERAL" not in page_sql
    assert "fabs.id ASC" in page_sql
    assert sql.endswith("LIMIT 25 OFFSET 0")


def test_search_and_filters_apply_before_pagination():
    latest = latest_templating()
    query = fabs._build_fab_list_query(
        7, None, None, None, None, None, None, None, latest,
    ).where(BusinessJob.name.ilike("%kitchen%"))
    paginated = fabs._paginate_fab_list_query(
        query, 0, 25, None, latest, needs_job_search=True,
    )
    page_sql = compile_sql(paginated).split("FROM (SELECT fabs.id AS id", 1)[1]

    assert "JOIN business_jobs" in page_sql
    assert "fabs.job_id = 7" in page_sql
    assert "business_jobs.name ILIKE '%%kitchen%%'" in page_sql
    assert "LIMIT 25 OFFSET 0" in page_sql


@pytest.mark.parametrize("skip, expected_ids", [
    (0, list(range(1, 26))),
    (25, list(range(26, 51))),
    (9975, list(range(9976, 10001))),
    (10000, []),
])
def test_page_selection_with_ten_thousand_rows(skip, expected_ids):
    table = Table(
        "fabs", MetaData(), Column("id", Integer, primary_key=True),
        Column("updated_at", DateTime), Column("created_at", DateTime),
    )
    engine = create_engine("sqlite:///:memory:")
    try:
        table.metadata.create_all(engine)
        latest = latest_templating()
        query = fabs._build_fab_list_query(
            None, None, None, None, None, None, None, None, latest,
        )
        paginated = fabs._paginate_fab_list_query(query, skip, 25, None, latest)
        page_query = next(
            element.element for element in visitors.iterate(paginated)
            if isinstance(element, Subquery) and element.name == "fab_page"
        )
        with engine.begin() as connection:
            connection.execute(table.insert(), [{"id": fab_id} for fab_id in range(1, 10001)])
            actual_ids = connection.execute(page_query).scalars().all()
        assert actual_ids == expected_ids
    finally:
        engine.dispose()


@pytest.mark.asyncio
async def test_list_enriches_only_page_and_counts_without_detail_joins(monkeypatch):
    page_result = Mock()
    page_result.all.return_value = [(SimpleNamespace(id=fab_id),) for fab_id in range(1, 26)]
    count_result = Mock()
    count_result.scalar.return_value = 10000
    db = SimpleNamespace(execute=AsyncMock(side_effect=[page_result, count_result]))
    monkeypatch.setattr(fabs, "_convert_fab_row_to_dict", lambda row: {"id": row[0].id})
    related = AsyncMock()
    plans = AsyncMock(return_value={})
    resurface = AsyncMock(return_value={})
    install = AsyncMock(return_value={})
    monkeypatch.setattr(fabs, "_batch_load_fab_related_data", related)
    monkeypatch.setattr(fabs, "get_plans_map_for_fabs", plans)
    monkeypatch.setattr(fabs, "_batch_load_resurface_scheduling_responses", resurface)
    monkeypatch.setattr(fabs, "_batch_load_install_scheduling_responses", install)
    kwargs = {
        name: parameter.default.default
        for name, parameter in inspect.signature(fabs.get_fabs).parameters.items()
        if name not in {"db", "current_user"}
    }
    kwargs.update(skip=0, limit=25, type="fab_id", db=db, current_user=SimpleNamespace(id=1))

    response = await fabs.get_fabs(**kwargs)

    assert response["data"]["total"] == 10000
    assert response["data"]["page"] == 1
    assert response["data"]["per_page"] == 25
    assert len(response["data"]["data"]) == 25
    assert len(related.await_args.args[1]) == 25
    for loader in (plans, resurface, install):
        assert loader.await_args.args[1] == list(range(1, 26))
    count_sql = compile_sql(db.execute.await_args_list[1].args[0])
    assert "count(fabs.id)" in count_sql
    assert "JOIN" not in count_sql
    assert "templatings" not in count_sql


def test_cnc_widget_excludes_install_completion_from_ids_and_count():
    metadata = MetaData()
    fab_table = Table(
        Fab.__tablename__, metadata, Column("id", Integer, primary_key=True),
        Column("current_stage", String), Column("cnc_linft", Float),
    )
    cnc_table = Table(
        fabs.CNCDrafting.__tablename__, metadata,
        Column("id", Integer, primary_key=True), Column("fab_id", Integer),
        Column("created_at", DateTime), Column("is_completed", Boolean),
    )
    engine = create_engine("sqlite:///:memory:")
    try:
        metadata.create_all(engine)
        with engine.begin() as connection:
            connection.execute(fab_table.insert(), [
                {"id": 1, "current_stage": "install_completion", "cnc_linft": 10},
                {"id": 2, "current_stage": "shop", "cnc_linft": 10},
                {"id": 3, "current_stage": "install_scheduling", "cnc_linft": 10},
                {"id": 4, "current_stage": None, "cnc_linft": 10},
                {"id": 5, "current_stage": "shop", "cnc_linft": 10},
                {"id": 6, "current_stage": "shop", "cnc_linft": 0},
                {"id": 7, "current_stage": "install_completion", "cnc_linft": 10},
                {"id": 8, "current_stage": "shop", "cnc_linft": None},
                {"id": 9, "current_stage": "shop", "cnc_linft": 10},
                {"id": 10, "current_stage": "shop", "cnc_linft": 10},
            ])
            connection.execute(cnc_table.insert(), [
                {"id": draft_id, "fab_id": fab_id, "created_at": datetime(2026, 10, 2), "is_completed": completed}
                for draft_id, fab_id, completed in [
                    (1, 1, False), (2, 2, False), (3, 4, False), (4, 5, True),
                    (5, 9, True), (6, 9, False), (7, 10, False), (8, 10, True),
                ]
            ])
            predicate = fabs._pending_cnc_widget_filter()
            ids = connection.execute(select(Fab.id).where(predicate).order_by(Fab.id)).scalars().all()
            count = connection.execute(select(func.count(Fab.id)).where(predicate)).scalar_one()

        assert ids == [2, 3, 4, 9]
        assert count == len(ids)
    finally:
        engine.dispose()


@pytest.mark.asyncio
async def test_cnc_widget_applies_exclusion_to_list_count_and_stage_totals(monkeypatch):
    result = Mock()
    result.all.return_value = []
    result.scalar.return_value = 0
    result.first.return_value = None
    db = SimpleNamespace(execute=AsyncMock(return_value=result))
    monkeypatch.setattr(fabs, "_batch_load_fab_related_data", AsyncMock())
    monkeypatch.setattr(fabs, "get_plans_map_for_fabs", AsyncMock(return_value={}))
    kwargs = {
        name: parameter.default.default
        for name, parameter in inspect.signature(fabs.get_fabs_for_cnc_widget).parameters.items()
        if name not in {"db", "current_user"}
    }
    kwargs.update(skip=0, limit=25, type="fab_id", current_stage="shop", db=db, current_user=SimpleNamespace(id=1))

    await fabs.get_fabs_for_cnc_widget(**kwargs)

    assert db.execute.await_count == 3
    for call in db.execute.await_args_list:
        assert "fabs.current_stage IS DISTINCT FROM 'install_completion'" in compile_sql(call.args[0])


@pytest.mark.asyncio
async def test_dashboard_cnc_count_and_recent_ids_use_same_exclusion():
    result = Mock()
    result.all.return_value = []
    result.scalar.return_value = 0
    db = SimpleNamespace(execute=AsyncMock(return_value=result))

    await fabs.get_all_stages(db=db, current_user=SimpleNamespace(id=1))

    cnc_queries = [
        compile_sql(call.args[0]) for call in db.execute.await_args_list
        if fabs.CNCDrafting.__tablename__ in compile_sql(call.args[0])
    ]
    assert len(cnc_queries) == 2
    assert "count(fabs.id)" in cnc_queries[0]
    for sql in cnc_queries:
        assert "fabs.current_stage IS DISTINCT FROM 'install_completion'" in sql


@pytest.mark.asyncio
@pytest.mark.parametrize("stage", [None, "shop", "install_scheduling", "install_completion"])
@pytest.mark.parametrize("status_id", [None, 2])
async def test_shop_est_widget_applies_exclusion_to_all_queries(monkeypatch, stage, status_id):
    result = Mock()
    result.all.return_value = []
    result.scalar.return_value = 0
    result.first.return_value = None
    db = SimpleNamespace(execute=AsyncMock(return_value=result))
    monkeypatch.setattr(fabs, "_batch_load_fab_related_data", AsyncMock())
    monkeypatch.setattr(fabs, "get_plans_map_for_fabs", AsyncMock(return_value={}))
    monkeypatch.setattr(fabs, "_batch_load_install_scheduling_responses", AsyncMock(return_value={}))
    kwargs = {
        name: parameter.default.default
        for name, parameter in inspect.signature(fabs.get_fabs_with_shop_est_completion).parameters.items()
        if name not in {"db", "current_user"}
    }
    kwargs.update(skip=0, limit=25, type="fab_id", current_stage=stage, status_id=status_id,
                  db=db, current_user=SimpleNamespace(id=1))

    response = await fabs.get_fabs_with_shop_est_completion(**kwargs)

    assert response["data"]["data"] == []
    assert db.execute.await_count == (3 if stage else 2)
    for call in db.execute.await_args_list:
        sql = compile_sql(call.args[0])
        assert "fabs.current_stage IS DISTINCT FROM 'install_completion'" in sql
        assert "fabs.status_id IN (0, 1)" in sql if status_id is None else "fabs.status_id = 2" in sql


@pytest.mark.asyncio
async def test_dashboard_install_scheduling_count_and_ids_match_widget_eligibility():
    result = Mock()
    result.all.return_value = []
    result.scalar.return_value = 0
    db = SimpleNamespace(execute=AsyncMock(return_value=result))

    await fabs.get_all_stages(db=db, current_user=SimpleNamespace(id=1))

    widget_queries = [
        compile_sql(call.args[0]) for call in db.execute.await_args_list
        if "fabs.shop_est_completion_date IS NOT NULL" in compile_sql(call.args[0])
    ]
    assert len(widget_queries) == 2
    assert "count(fabs.id)" in widget_queries[0]
    for sql in widget_queries:
        assert "fabs.current_stage IS DISTINCT FROM 'install_completion'" in sql
        assert "fabs.status_id IN (0, 1)" in sql
        assert "install_schedulings.installer_id IS NOT NULL" in sql
        assert "install_schedulings.scheduled_install_date IS NOT NULL" in sql