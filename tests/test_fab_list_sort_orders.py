import src.app.database.model_registry  # noqa: F401
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from src.app.database.fab import Fab
from src.app.interface.generated_schemas import Templating
from src.app.routers import fabs


def compiled(sort_by):
    latest_templating = (
        select(Templating).where(Templating.fab_id == Fab.id).order_by(Templating.id.desc()).limit(1).lateral("latest_templating")
    )
    query = fabs._build_fab_list_query(None, None, None, None, None, None, None, None, latest_templating)
    paged = fabs._paginate_fab_list_query(query, 25, 25, None, latest_templating, sort_by=sort_by)
    return " ".join(str(paged.compile(dialect=postgresql.dialect())).split())


def test_view_all_fabs_lists_newest_fab_first():
    sql = compiled("fab_id_desc")
    # Both the page selection and the final rows use the override.
    assert sql.count("ORDER BY fabs.id DESC") == 2
    assert "fabs.updated_at ASC" not in sql


def test_job_status_sorts_by_job_number_numerically():
    sql = compiled("job_number_desc")
    assert sql.count("ORDER BY length(business_jobs.job_number) DESC NULLS LAST, business_jobs.job_number DESC NULLS LAST, fabs.id DESC") == 2


def test_default_keeps_stage_ordering():
    assert "fabs.updated_at ASC NULLS FIRST" in compiled(None)


def test_latest_assignee_filter_matches_most_recent_record():
    from src.app.database.cnc import CNCDrafting

    sql = " ".join(str(fabs._latest_assignee_condition(CNCDrafting, 7).compile(dialect=postgresql.dialect())).split())
    assert "ORDER BY cnc_draftings.created_at DESC, cnc_draftings.id DESC LIMIT" in sql
    assert sql.endswith("= %(param_1)s") or "= %(" in sql
    unassigned = " ".join(str(fabs._latest_assignee_condition(CNCDrafting, 0).compile(dialect=postgresql.dialect())).split())
    assert unassigned.endswith("IS NULL")


def test_sct_queue_orders_revised_fabs_by_revision_submission():
    sql = " ".join(str(fabs._apply_pagination_and_ordering(select(Fab.id), 0, 25, "sales_ct", None)
                       .compile(dialect=postgresql.dialect())).split())
    assert "ORDER BY greatest(fabs.draft_completed_date, (SELECT max(revisions.actual_end_date)" in sql
    assert "revisions.is_completed IS true" in sql
