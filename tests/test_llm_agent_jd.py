"""Agent JD pipeline tests with mocked HTTP only."""

from __future__ import annotations

import io
import json
import os
from unittest.mock import MagicMock, patch

import pytest

from resume_rewriter.llm_agent_jd import (
    AgentJDRewriteError,
    artifact_to_json_dict,
    rewrite_with_agent_jd,
    run_agent_jd_pipeline,
)


def _mock_urlopen_json_sequence(*payloads: dict) -> MagicMock:
    side_effect_items = []
    for payload in payloads:
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = io.BytesIO(json.dumps(payload).encode("utf-8"))
        mock_cm.__exit__.return_value = None
        side_effect_items.append(mock_cm)
    mocked = MagicMock()
    mocked.side_effect = side_effect_items
    return mocked


@patch("resume_rewriter.llm_agent_jd.urllib.request.urlopen")
def test_run_agent_jd_pipeline_success(mock_urlopen: MagicMock) -> None:
    analyze_content = {
        "requirements": [{"text": "Production deployment", "priority": "must"}],
        "gaps": [{"requirement": "Production deployment", "reason": "Not explicit"}],
        "rewrite_plan": [{"instruction": "Emphasize deployment context"}],
    }
    rewrite_content = {"rewritten_bullet": "Built ML model integrated into production pipeline."}
    mock_urlopen.side_effect = _mock_urlopen_json_sequence(
        {"choices": [{"message": {"content": json.dumps(analyze_content)}}]},
        {"choices": [{"message": {"content": json.dumps(rewrite_content)}}]},
    ).side_effect

    with patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "sk-test", "OPENAI_MODEL": "gpt-test"},
        clear=False,
    ):
        artifact = run_agent_jd_pipeline("Built ML model.", "Need production ML experience.")

    assert artifact.original == "Built ML model."
    assert artifact.rewritten_bullet == "Built ML model integrated into production pipeline."
    assert len(artifact.requirements) == 1
    assert len(artifact.gaps) == 1
    assert len(artifact.rewrite_plan) == 1
    assert artifact.risk_flags == []


def test_run_agent_jd_pipeline_empty_input_raises() -> None:
    with pytest.raises(AgentJDRewriteError, match="Input bullet is empty"):
        run_agent_jd_pipeline("   ", "Some JD text")


def test_run_agent_jd_pipeline_missing_key_raises() -> None:
    old = os.environ.pop("OPENAI_API_KEY", None)
    try:
        with pytest.raises(AgentJDRewriteError, match="OPENAI_API_KEY"):
            run_agent_jd_pipeline("Built ML model.", "Need production ML experience.")
    finally:
        if old is not None:
            os.environ["OPENAI_API_KEY"] = old


@patch("resume_rewriter.llm_agent_jd.urllib.request.urlopen")
def test_run_agent_jd_pipeline_invalid_analyze_json_raises(mock_urlopen: MagicMock) -> None:
    mock_urlopen.side_effect = _mock_urlopen_json_sequence(
        {"choices": [{"message": {"content": '{"requirements": "bad"}'}}]},
    ).side_effect

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=False):
        with pytest.raises(AgentJDRewriteError, match="Invalid requirements field"):
            run_agent_jd_pipeline("Built ML model.", "Need production ML experience.")


@patch("resume_rewriter.llm_agent_jd.urllib.request.urlopen")
def test_rewrite_with_agent_jd_returns_rewriteresult(mock_urlopen: MagicMock) -> None:
    analyze_content = {
        "requirements": [{"text": "Latency awareness", "priority": "must"}],
        "gaps": [{"requirement": "Latency awareness", "reason": "Not explicit"}],
        "rewrite_plan": [{"instruction": "Mention latency constraints if present"}],
    }
    rewrite_content = {"rewritten_bullet": "Built ML model while maintaining latency constraints for serving."}
    mock_urlopen.side_effect = _mock_urlopen_json_sequence(
        {"choices": [{"message": {"content": json.dumps(analyze_content)}}]},
        {"choices": [{"message": {"content": json.dumps(rewrite_content)}}]},
    ).side_effect

    with patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "sk-test", "OPENAI_MODEL": "gpt-test"},
        clear=False,
    ):
        result = rewrite_with_agent_jd("Built ML model.", "Need low-latency production systems.")

    assert result.original == "Built ML model."
    assert result.rewritten == "Built ML model while maintaining latency constraints for serving."
    assert "Agent JD rewrite (gpt-test)" in result.changes
    assert "2-step pipeline: analyze_plan -> rewrite" in result.changes


@patch("resume_rewriter.llm_agent_jd.urllib.request.urlopen")
def test_artifact_to_json_dict_contains_nested_lists(mock_urlopen: MagicMock) -> None:
    analyze_content = {
        "requirements": [{"text": "Production deployment", "priority": "must"}],
        "gaps": [{"requirement": "Production deployment", "reason": "Not explicit"}],
        "rewrite_plan": [{"instruction": "Emphasize deployment context"}],
    }
    rewrite_content = {"rewritten_bullet": "Built ML model integrated into production pipeline."}
    mock_urlopen.side_effect = _mock_urlopen_json_sequence(
        {"choices": [{"message": {"content": json.dumps(analyze_content)}}]},
        {"choices": [{"message": {"content": json.dumps(rewrite_content)}}]},
    ).side_effect

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=False):
        artifact = run_agent_jd_pipeline("Built ML model.", "Need production ML experience.")
    payload = artifact_to_json_dict(artifact)

    assert payload["original"] == "Built ML model."
    assert isinstance(payload["requirements"], list)
    assert payload["requirements"][0]["text"] == "Production deployment"

