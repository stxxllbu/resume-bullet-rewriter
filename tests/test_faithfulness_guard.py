"""Tests for rule-based faithfulness guard."""

from __future__ import annotations

from faithfulness_guard import run_faithfulness_guard


def test_guard_flags_new_number_as_metric() -> None:
    flags = run_faithfulness_guard(
        "Built ML model for ranking.",
        "Built ML model for ranking and improved CTR by 12%.",
    )
    assert "fabricated_metric" in flags


def test_guard_flags_new_scale_term() -> None:
    flags = run_faithfulness_guard(
        "Maintained data pipeline.",
        "Maintained large-scale data pipeline.",
    )
    assert "fabricated_scale" in flags


def test_guard_flags_new_tool_term_case_insensitive() -> None:
    flags = run_faithfulness_guard(
        "Built batch processing job.",
        "Built batch processing job on AWS.",
    )
    assert "fabricated_tooling" in flags


def test_guard_returns_no_flags_when_no_new_risky_claims() -> None:
    flags = run_faithfulness_guard(
        "Built ML model for ranking.",
        "Built ML model for ranking and improved results.",
    )
    assert flags == []

