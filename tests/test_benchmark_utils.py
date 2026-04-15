"""Unit tests for benchmark_utils V0 helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from benchmark_utils import (
    load_bullets,
    parse_backends,
    run_one,
    summarize_results,
)
from rewriter import RewriteResult


def test_load_bullets_skips_empty_lines(tmp_path: Path) -> None:
    p = tmp_path / "bullets.txt"
    p.write_text("a\n\n  b  \n", encoding="utf-8")
    assert load_bullets(str(p)) == ["a", "b"]


def test_parse_backends_valid_and_trimmed() -> None:
    assert parse_backends("rules, openai,ollama") == ["rules", "openai", "ollama"]


def test_parse_backends_invalid_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported backend"):
        parse_backends("rules,bad")


def test_run_one_success_row_shape() -> None:
    with patch("benchmark_utils.rewrite_with_backend") as mock_dispatch:
        mock_dispatch.return_value = RewriteResult(
            original="x",
            rewritten="y",
            changes=["ok"],
        )
        row = run_one("input bullet", "rules", 3)

    assert row["index"] == 3
    assert row["backend"] == "rules"
    assert row["input"] == "input bullet"
    assert row["success"] is True
    assert row["rewritten"] == "y"
    assert row["changes"] == ["ok"]
    assert row["error_type"] is None
    assert row["quality"]["len_in"] > 0


def test_run_one_error_row_shape() -> None:
    with patch("benchmark_utils.rewrite_with_backend") as mock_dispatch:
        mock_dispatch.side_effect = ValueError("Unsupported backend")
        row = run_one("input bullet", "bad", 1)

    assert row["success"] is False
    assert row["rewritten"] is None
    assert row["error_type"] == "ValueError"
    assert "Unsupported backend" in row["error_message"]
    assert row["quality"] is None


def test_summarize_results_aggregates() -> None:
    rows = [
        {
            "backend": "rules",
            "success": True,
            "latency_ms": 1.0,
            "quality": {"added_number_flag": False},
        },
        {
            "backend": "rules",
            "success": False,
            "latency_ms": 3.0,
            "quality": None,
        },
        {
            "backend": "openai",
            "success": True,
            "latency_ms": 10.0,
            "quality": {"added_number_flag": True},
        },
    ]
    s = summarize_results(rows)
    assert s["total_rows"] == 3
    assert s["by_backend"]["rules"]["total"] == 2
    assert s["by_backend"]["rules"]["success_count"] == 1
    assert s["by_backend"]["rules"]["fail_count"] == 1
    assert s["by_backend"]["openai"]["added_number_rate"] == 1.0
