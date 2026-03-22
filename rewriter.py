"""
Rule-based rewrite engine (V1): deterministic, conservative, no external APIs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from rules import LEADING_RULES, apply_rule_once, ordered_phrase_rules


@dataclass(frozen=True)
class RewriteResult:
    """One bullet before/after rewrite plus human-readable rule hits."""

    original: str
    rewritten: str
    changes: list[str] = field(default_factory=list)


def normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace; strip ends."""
    return " ".join(text.split())


def _ensure_sentence_case(text: str) -> str:
    """Capitalize the first alphabetic character; leave the rest unchanged."""
    for i, ch in enumerate(text):
        if ch.isalpha():
            return text[:i] + ch.upper() + text[i + 1 :]
    return text


def _ensure_terminal_period(text: str) -> str:
    """End with a single period if the bullet has no sentence-ending punctuation."""
    stripped = text.rstrip()
    if not stripped:
        return stripped
    if stripped[-1] in ".!?":
        return stripped
    return stripped + "."


def rewrite(raw: str) -> RewriteResult:
    """
    Apply phrase rules, then leading rules, then light punctuation cleanup.

    Does not invent content: only substitutions defined in ``rules.py``.
    """
    original = normalize_whitespace(raw)
    if not original:
        return RewriteResult(original="", rewritten="", changes=["(empty input: skipped)"])

    changes: list[str] = []
    current = original

    for rule in ordered_phrase_rules():
        current, n, note = apply_rule_once(current, rule)
        if n and note:
            changes.append(note)

    for rule in LEADING_RULES:
        current, n, note = apply_rule_once(current, rule)
        if n and note:
            changes.append(note)

    current = _ensure_sentence_case(current)
    current = _ensure_terminal_period(current)

    if not changes:
        changes.append("(no matching rules; whitespace and punctuation normalized only)")

    return RewriteResult(original=original, rewritten=current, changes=changes)
