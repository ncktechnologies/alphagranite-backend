import pytest

from src.app.mcp.report_tools import NLToolSelection


@pytest.mark.asyncio
async def test_get_mcp_tools_returns_catalog(client, test_db, monkeypatch):
    from tests.conftest import get_test_token_header
    from src.app.routers import mcp as mcp_router

    async def fake_save_audit_trail(*args, **kwargs):
        return {"audit_id": 1}

    monkeypatch.setattr(mcp_router, "save_audit_trail", fake_save_audit_trail)

    auth_headers = await get_test_token_header(client)
    response = await client.get("/api/v1/mcp/tools", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert any(tool["name"] == "owner.overview" for tool in body["data"])
    assert any(tool["name"] == "owner.largest_jobs" for tool in body["data"])
    assert any(tool["name"] == "owner.management_packet" for tool in body["data"])


@pytest.mark.asyncio
async def test_get_mcp_tool_details_returns_schema(client, test_db):
    from tests.conftest import get_test_token_header

    auth_headers = await get_test_token_header(client)
    response = await client.get("/api/v1/mcp/tools/owner.overview", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == "owner.overview"
    assert "input_schema" in body["data"]
    assert "sample_params" in body["data"]


@pytest.mark.asyncio
async def test_invoke_mcp_tool_returns_wrapped_result(client, test_db, monkeypatch):
    from tests.conftest import get_test_token_header
    from src.app.routers import mcp as mcp_router

    async def fake_invoke_report_tool(name, params, *, db, current_user):
        assert name == "owner.overview"
        assert params["start_date"] == "2026-06-01"
        return {"kpis": {"total_jobs": 7}}

    async def fake_save_audit_trail(*args, **kwargs):
        return {"audit_id": 99}

    monkeypatch.setattr(mcp_router, "invoke_report_tool", fake_invoke_report_tool)
    monkeypatch.setattr(mcp_router, "save_audit_trail", fake_save_audit_trail)

    auth_headers = await get_test_token_header(client)
    response = await client.post(
        "/api/v1/mcp/tools/owner.overview/invoke",
        headers=auth_headers,
        json={"params": {"start_date": "2026-06-01", "end_date": "2026-06-30"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["tool"] == "owner.overview"
    assert body["data"]["result"]["kpis"]["total_jobs"] == 7


@pytest.mark.asyncio
async def test_ask_mcp_bi_question_routes_and_summarizes(client, test_db, monkeypatch):
    from tests.conftest import get_test_token_header
    from src.app.routers import mcp as mcp_router

    def fake_select_tool_for_question(question: str):
        assert "redo" in question.lower()
        return NLToolSelection(
            tool_name="owner.redo_analysis",
            confidence="high",
            rationale="Matched redo terms.",
            params={"start_date": "2026-06-01", "end_date": "2026-06-30", "top_n": 10},
        )

    async def fake_invoke_report_tool(name, params, *, db, current_user):
        assert name == "owner.redo_analysis"
        return {
            "summary": {"redo_rate_percent": 4.2, "total_fabs": 100, "revision_events": 9},
            "top_accounts_with_redo": [{"account_name": "ABC Stone", "redo_count": 4}],
            "top_jobs_with_redo": [{"job_number": "J-100", "job_name": "Main Lobby", "redo_count": 2}],
        }

    def fake_summarize_tool_result(tool_name: str, result: dict):
        assert tool_name == "owner.redo_analysis"
        return ["Redo rate is 4.2%.", "Top redo account is ABC Stone."]

    async def fake_save_audit_trail(*args, **kwargs):
        return {"audit_id": 5}

    monkeypatch.setattr(mcp_router, "select_tool_for_question", fake_select_tool_for_question)
    monkeypatch.setattr(mcp_router, "invoke_report_tool", fake_invoke_report_tool)
    monkeypatch.setattr(mcp_router, "summarize_tool_result", fake_summarize_tool_result)
    monkeypatch.setattr(mcp_router, "save_audit_trail", fake_save_audit_trail)

    auth_headers = await get_test_token_header(client)
    response = await client.post(
        "/api/v1/mcp/ask",
        headers=auth_headers,
        json={"question": "What are the redo hotspots this month?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["matched_tool"] == "owner.redo_analysis"
    assert body["data"]["confidence"] == "high"
    assert body["data"]["insights"][0] == "Redo rate is 4.2%."


@pytest.mark.asyncio
async def test_ask_mcp_bi_question_accepts_param_overrides(client, test_db, monkeypatch):
    from tests.conftest import get_test_token_header
    from src.app.routers import mcp as mcp_router

    def fake_select_tool_for_question(question: str):
        return NLToolSelection(
            tool_name="owner.install_performance",
            confidence="medium",
            rationale="Matched installer productivity terms.",
            params={"start_date": "2026-06-01", "end_date": "2026-06-30", "top_n": 25},
        )

    async def fake_invoke_report_tool(name, params, *, db, current_user):
        assert params["top_n"] == 5
        return {"summary": {"installer_count": 5}}

    def fake_summarize_tool_result(tool_name: str, result: dict):
        return ["Installer portfolio summary generated."]

    async def fake_save_audit_trail(*args, **kwargs):
        return {"audit_id": 6}

    monkeypatch.setattr(mcp_router, "select_tool_for_question", fake_select_tool_for_question)
    monkeypatch.setattr(mcp_router, "invoke_report_tool", fake_invoke_report_tool)
    monkeypatch.setattr(mcp_router, "summarize_tool_result", fake_summarize_tool_result)
    monkeypatch.setattr(mcp_router, "save_audit_trail", fake_save_audit_trail)

    auth_headers = await get_test_token_header(client)
    response = await client.post(
        "/api/v1/mcp/ask",
        headers=auth_headers,
        json={"question": "Show installer productivity this month", "params": {"top_n": 5}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["resolved_params"]["top_n"] == 5
    assert body["data"]["matched_tool"] == "owner.install_performance"