from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from src.app.database.fab import Fab
from src.app.routers.fabs import (
    _install_status_filter,
    _installer_assignment_filter,
    _installer_install_scheduling_filter,
)


def test_today_installer_filter_uses_assigned_scheduling_date_without_extra_gates():
    query = select(Fab.id).where(_installer_install_scheduling_filter(57, "today"))
    sql = str(
        query.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "install_schedulings.installer_id = 57" in sql
    assert f"CAST(install_schedulings.scheduled_install_date AS DATE) = '{date.today().isoformat()}'" in sql
    assert "interval '16 hours'" not in sql
    assert "install_completions" not in sql


def test_installer_assignment_filter_matches_primary_and_extra_crew():
    query = select(Fab.id).where(_installer_assignment_filter(57))
    sql = str(
        query.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "install_schedulings.installer_id = 57" in sql
    assert "install_schedulings.extra_crew_1_id = 57" in sql
    assert "install_schedulings.extra_crew_2_id = 57" in sql
    assert "install_schedulings.extra_crew_3_id = 57" in sql


def test_complete_install_status_requires_shop_plans_done_and_install_complete():
    query = select(Fab.id).where(_install_status_filter("complete"))
    sql = str(
        query.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "shop_cut_plans.fab_id = fabs.id" in sql
    assert "coalesce(shop_cut_plans.work_percentage, 0) < 100" in sql
    assert "install_completions.fab_id = fabs.id" in sql
    assert "install_completions.is_completed IS true" in sql
    assert "install_schedulings.fab_id = fabs.id" in sql
    assert "install_schedulings.is_completed IS true" in sql


def test_incomplete_install_status_is_inverse_of_complete_status():
    query = select(Fab.id).where(_install_status_filter("incomplete"))
    sql = str(
        query.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "NOT" in sql
    assert "install_completions.is_completed IS true" in sql
