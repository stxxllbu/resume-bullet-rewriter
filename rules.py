"""
Conservative, deterministic rewrite patterns.

Rules only swap weak verbs/phrasing; they do not add metrics, numbers, or impact claims.
Order matters: phrase rules are applied in list order (longer / more specific first).
"""

from __future__ import annotations

import re
from typing import NamedTuple


class PhraseRule(NamedTuple):
    """Regex pattern, replacement, and a short note for the change log."""

    pattern: str
    replacement: str
    description: str


# Applied in order, anywhere in the bullet (word-boundary safe).
PHRASE_RULES: list[PhraseRule] = [
    PhraseRule(
        r"\bwas involved in\b",
        "participated in",
        "Replaced 'was involved in' with 'participated in'",
    ),
    PhraseRule(
        r"\bworked on\b",
        "contributed to",
        "Replaced 'worked on' with 'contributed to'",
    ),
    PhraseRule(
        r"\bhelped with\b",
        "supported",
        "Replaced 'helped with' with 'supported'",
    ),
    PhraseRule(
        r"\bhelped to\b",
        "supported",
        "Replaced 'helped to' with 'supported'",
    ),
    PhraseRule(
        r"\bassisted with\b",
        "supported",
        "Replaced 'assisted with' with 'supported'",
    ),
    PhraseRule(
        r"\bhelped build\b",
        "contributed to building",
        "Replaced 'helped build' with 'contributed to building'",
    ),
    PhraseRule(
        r"\bin order to\b",
        "to",
        "Tightened 'in order to' to 'to'",
    ),
]

# Applied only at the start of the bullet (after whitespace normalization).
LEADING_RULES: list[PhraseRule] = [
    PhraseRule(
        r"^was part of\b",
        "Participated in",
        "Reworded leading 'Was part of' to 'Participated in'",
    ),
    PhraseRule(
        r"^did\b",
        "Completed",
        "Upgraded leading 'Did' to 'Completed'",
    ),
    PhraseRule(
        r"^made\b",
        "Developed",
        "Upgraded leading 'Made' to 'Developed'",
    ),
    PhraseRule(
        r"^used\b",
        "Applied",
        "Upgraded leading 'Used' to 'Applied'",
    ),
]


def _phrase_key(rule: PhraseRule) -> tuple[int, str]:
    """Sort key: longer patterns first for safer overlapping matches."""
    return (-len(rule.pattern), rule.pattern)


def ordered_phrase_rules() -> list[PhraseRule]:
    """Phrase rules with stable ordering (longer patterns first)."""
    return sorted(PHRASE_RULES, key=_phrase_key)


def apply_rule_once(
    text: str,
    rule: PhraseRule,
    *,
    flags: int = re.IGNORECASE,
) -> tuple[str, int, str | None]:
    """
    Apply one substitution across the whole string.

    Returns (new_text, match_count, description_or_none).
    """
    new_text, n = re.subn(rule.pattern, rule.replacement, text, flags=flags)
    if n == 0:
        return text, 0, None
    note = rule.description if n == 1 else f"{rule.description} ({n}×)"
    return new_text, n, note
