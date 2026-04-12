"""Golden-path tests for the rule-based rewrite engine (deterministic)."""

from __future__ import annotations

import pytest

from rewriter import normalize_whitespace, rewrite


def test_normalize_whitespace_collapses_and_strips() -> None:
    assert normalize_whitespace("  a   b  ") == "a b"


def test_rewrite_empty_input() -> None:
    r = rewrite("")
    assert r.original == ""
    assert r.rewritten == ""
    assert r.changes == ["(empty input: skipped)"]


def test_rewrite_worked_on_phrase() -> None:
    r = rewrite("worked on the internal API")
    assert r.original == "worked on the internal API"
    assert r.rewritten == "Contributed to the internal API."
    assert any("worked on" in c and "contributed to" in c for c in r.changes)


def test_rewrite_helped_with() -> None:
    r = rewrite("helped with onboarding documentation")
    assert r.rewritten == "Supported onboarding documentation."
    assert any("helped with" in c.lower() for c in r.changes)


def test_rewrite_was_part_of_leading_rule() -> None:
    r = rewrite("Was part of the release rotation")
    assert r.rewritten == "Participated in the release rotation."
    assert any("Was part of" in c or "part of" in c for c in r.changes)


def test_rewrite_no_rule_match_still_normalizes_period() -> None:
    r = rewrite("hello")
    assert r.original == "hello"
    assert r.rewritten == "Hello."
    assert any("no matching rules" in c for c in r.changes)


def test_rewrite_idempotent_shape_for_stable_bullet() -> None:
    """Same input twice should yield identical results."""
    a = rewrite("worked on the internal API")
    b = rewrite("worked on the internal API")
    assert a == b
