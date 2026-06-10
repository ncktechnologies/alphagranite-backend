from src.app.service.ai_provider import (
    _anthropic_agent_id,
    _extract_text_from_anthropic_payload,
    _normalize_advisor_output,
    _normalize_focus,
    _normalize_response_mode,
)


def test_normalize_advisor_output_supports_rich_schema():
    raw = {
        "executive_summary": "Top job concentration is high.",
        "what_this_means": "Revenue concentration risk is elevated.",
        "key_findings": ["Top 3 jobs drive 52% of volume."],
        "metric_breakdown": ["rows: 25", "total_sqft: 18240"],
        "risk_flags": ["Concentration risk"],
        "recommended_actions": ["Diversify pipeline mix"],
        "assumptions_and_gaps": ["No margin by job in payload"],
        "next_questions": ["Do you want margin ranking too?"],
        "priority": "high",
        "conversation_reply": "Top job concentration is high and needs action.",
        "evidence": ["summary.row_count", "rows[0].total_sqft"],
    }

    normalized = _normalize_advisor_output(raw)

    assert normalized is not None
    assert normalized["executive_summary"] == "Top job concentration is high."
    assert normalized["summary"] == "Top job concentration is high."
    assert normalized["risk_flags"][0] == "Concentration risk"
    assert normalized["evidence"][0] == "summary.row_count"


def test_normalize_advisor_output_supports_legacy_schema_aliases():
    raw = {
        "summary": "Legacy summary",
        "what_this_means": "Legacy implications",
        "likely_causes": ["Cause A"],
        "recommended_actions": ["Action A"],
        "priority": "medium",
        "follow_up_question": "Need more detail?",
        "conversation_reply": "Legacy conversation reply",
    }

    normalized = _normalize_advisor_output(raw)

    assert normalized is not None
    assert normalized["executive_summary"] == "Legacy summary"
    assert normalized["risk_flags"][0] == "Cause A"
    assert normalized["follow_up_question"] == "Need more detail?"


def test_normalize_response_mode_and_focus_defaults():
    assert _normalize_response_mode("DEEP") == "deep"
    assert _normalize_response_mode("invalid-mode") == "standard"
    assert _normalize_focus("Finance") == "finance"
    assert _normalize_focus("anything") == "mixed"


def test_extract_text_from_anthropic_payload_handles_content_blocks():
    payload = {
        "content": [
            {"type": "text", "text": "{\"tool_name\":\"owner.overview\",\"confidence\":\"high\",\"rationale\":\"ok\",\"params\":{}}"}
        ]
    }

    text = _extract_text_from_anthropic_payload(payload)

    assert "tool_name" in text


def test_extract_text_from_anthropic_payload_handles_nested_result():
    payload = {
        "result": {
            "content": [
                {"type": "text", "text": "{\"executive_summary\":\"ok\"}"}
            ]
        }
    }

    text = _extract_text_from_anthropic_payload(payload)

    assert "executive_summary" in text


def test_anthropic_agent_id_reads_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_AGENT_ID", "agent_123")
    assert _anthropic_agent_id() == "agent_123"
