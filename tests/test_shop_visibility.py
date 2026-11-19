from datetime import datetime

import pytest
from sqlalchemy import Boolean, Column, DateTime, Integer, MetaData, String, Table, create_engine, select

from src.app.database.fab import Fab
from src.app.database.shop_cut_plan import ShopCutPlan
from src.app.routers import fabs

EST = datetime(2026, 10, 30)

# fab_id: (current_stage, cutlist_complete, shop_est_completion_date, plan work percentages)
FABS = {
    1: ("shop", True, None, [100, 100]),               # done, no date      -> shown
    2: ("shop", True, EST, [100, 100]),                # done, dated        -> hidden
    3: ("cut_list", True, None, [100, 100]),           # done, no date      -> shown (used to drop off)
    4: ("install_scheduling", True, None, [100]),      # done, no date      -> shown (used to drop off)
    5: ("install_completion", True, None, [100]),      # installed          -> hidden
    6: ("install_scheduling", True, EST, [100]),       # done, dated        -> hidden
    7: ("install_scheduling", True, EST, [100, 40]),   # still in progress  -> shown
    8: ("shop", True, None, []),                       # no plans yet       -> shown
    9: ("templating", False, None, []),                # not in shop        -> hidden
}


@pytest.fixture
def connection():
    # Only the columns the visibility rule reads (the real fabs table uses JSONB, which SQLite lacks).
    metadata = MetaData()
    fab_table = Table(
        Fab.__tablename__, metadata, Column("id", Integer, primary_key=True),
        Column("current_stage", String), Column("cutlist_complete", Boolean),
        Column("shop_est_completion_date", DateTime),
    )
    plan_table = Table(
        ShopCutPlan.__tablename__, metadata, Column("id", Integer, primary_key=True),
        Column("fab_id", Integer), Column("work_percentage", Integer),
    )
    engine = create_engine("sqlite://")
    metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(fab_table.insert(), [
            {"id": fab_id, "current_stage": stage, "cutlist_complete": cutlist_complete, "shop_est_completion_date": est}
            for fab_id, (stage, cutlist_complete, est, _) in FABS.items()
        ])
        conn.execute(plan_table.insert(), [
            {"fab_id": fab_id, "work_percentage": percentage}
            for fab_id, (_, _, _, percentages) in FABS.items()
            for percentage in percentages
        ])
        yield conn
    engine.dispose()


def test_shop_list_keeps_completed_fabs_until_est_date_is_set(connection):
    visible = connection.execute(
        select(Fab.id).where(fabs._stage_filter_condition("shop")).order_by(Fab.id)
    ).scalars().all()

    assert visible == [1, 3, 4, 7, 8]


@pytest.mark.parametrize("est, percentages, expected", [
    (None, [100, 100], True),
    ("2026-10-30", [100, 100], False),
    (None, [100, 40], False),
    (None, [100, None], False),
    (None, [], False),
])
def test_needs_shop_est_date(est, percentages, expected):
    plans = [{"work_percentage": p} for p in percentages]
    assert fabs._needs_shop_est_date({"shop_est_completion_date": est}, plans) is expected
