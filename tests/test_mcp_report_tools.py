from src.app.mcp.report_tools import select_tool_for_question, suggest_tools_for_question, summarize_tool_result


def test_select_tool_for_square_footage_ranking_question_prefers_largest_jobs():
    selection = select_tool_for_question("List the jobs with the most square footage")

    assert selection.tool_name == "owner.largest_jobs"
    assert selection.confidence == "high"


def test_suggest_tools_for_square_footage_ranking_includes_largest_jobs_first():
    ranked = suggest_tools_for_question("Top 10 jobs by sqft this month", limit=5)

    assert ranked
    assert ranked[0]["tool_name"] == "owner.largest_jobs"


def test_summarize_largest_jobs_result_returns_ranked_insights():
    result = {
        "summary": {"row_count": 2},
        "rows": [
            {"job_number": "J-1001", "job_name": "City Hall", "total_sqft": 1240.5},
            {"job_number": "J-1002", "job_name": "Airport Wing", "total_sqft": 1100.0},
        ],
    }

    insights = summarize_tool_result("owner.largest_jobs", result)

    assert insights[0] == "Returned 2 ranked jobs by square footage."
    assert "J-1001" in insights[1]
    assert "1240.5 sqft" in insights[1]


def test_summarize_largest_jobs_result_handles_empty_rows():
    insights = summarize_tool_result("owner.largest_jobs", {"summary": {"row_count": 0}, "rows": []})

    assert insights == ["No job-level square-footage rows were returned for the selected filters."]
