"""I/O behavior tests for main.py agent_jd integration."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import resume_rewriter.main as main
from resume_rewriter.agent_jd_types import AgentJDArtifact
from resume_rewriter.rewriter import RewriteResult


def test_main_agent_jd_requires_jd_file(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("sys.argv", ["main.py", "--backend", "agent_jd", "hello"]):
        with pytest.raises(SystemExit) as exc:
            main.main()
    assert exc.value.code == 2
    assert "--jd-file is required" in capsys.readouterr().err


def test_main_agent_jd_json_prints_artifact(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    jd = tmp_path / "jd.txt"
    jd.write_text("Need production ML systems.", encoding="utf-8")
    artifact = AgentJDArtifact(
        original="Built ML model.",
        jd_text="Need production ML systems.",
        requirements=[],
        gaps=[],
        rewrite_plan=[],
        rewritten_bullet="Built ML model for production pipeline.",
        risk_flags=[],
    )
    with patch("resume_rewriter.main.run_agent_jd_pipeline", return_value=artifact) as mock_pipeline:
        with patch(
            "sys.argv",
            [
                "main.py",
                "--backend",
                "agent_jd",
                "--jd-file",
                str(jd),
                "--json",
                "Built ML model.",
            ],
        ):
            main.main()

    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["original"] == "Built ML model."
    assert payload["rewritten_bullet"] == "Built ML model for production pipeline."
    mock_pipeline.assert_called_once()


def test_main_agent_jd_uses_rewriteresult_for_normal_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    jd = tmp_path / "jd.txt"
    jd.write_text("Need production ML systems.", encoding="utf-8")
    with patch("resume_rewriter.main.rewrite_with_agent_jd") as mock_rewrite:
        mock_rewrite.return_value = RewriteResult(
            original="Built ML model.",
            rewritten="Built ML model for production pipeline.",
            changes=["Agent JD rewrite (gpt-test)"],
        )
        with patch(
            "sys.argv",
            [
                "main.py",
                "--backend",
                "agent_jd",
                "--jd-file",
                str(jd),
                "Built ML model.",
            ],
        ):
            main.main()

    out = capsys.readouterr().out
    assert "Original Bullet:" in out
    assert "Rewritten Bullet:" in out
    mock_rewrite.assert_called_once_with("Built ML model.", "Need production ML systems.")

