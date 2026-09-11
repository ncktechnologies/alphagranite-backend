from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from src.app.database.fab import Fab
from src.app.routers.fabs import _installer_install_scheduling_filter


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