"""
Rule-based faithfulness checks for rewritten bullets.
"""

from __future__ import annotations

import re
from typing import List, Set

_SCALE_TERMS = (
    "large-scale",
    "large scale",
    "millions",
    "global",
)

_TOOL_TERMS = (
    "aws",
    "spark",
    "kubernetes",
    "k8s",
    "airflow",
    "databricks",
    "snowflake",
    "hadoop",
    "pytorch",
    "tensorflow",
)


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _extract_numbers(text: str) -> Set[str]:
    # Matches plain numbers, decimals, and percentages (e.g., 12, 12.5, 12%).
    return set(re.findall(r"\b\d+(?:\.\d+)?%?\b", text))


def _new_phrase_hits(original: str, rewritten: str, phrases: tuple) -> List[str]:
    original_norm = _normalize(original)
    rewritten_norm = _normalize(rewritten)
    hits: List[str] = []
    for phrase in phrases:
        if phrase in rewritten_norm and phrase not in original_norm:
            hits.append(phrase)
    return hits


def run_faithfulness_guard(original: str, rewritten: str) -> List[str]:
    """
    Return risk flags when rewritten text introduces unsupported claims.
    """
    flags: List[str] = []

    original_numbers = _extract_numbers(original)
    rewritten_numbers = _extract_numbers(rewritten)
    new_numbers = rewritten_numbers - original_numbers
    if new_numbers:
        flags.append("fabricated_metric")

    new_scale_terms = _new_phrase_hits(original, rewritten, _SCALE_TERMS)
    if new_scale_terms:
        flags.append("fabricated_scale")

    new_tool_terms = _new_phrase_hits(original, rewritten, _TOOL_TERMS)
    if new_tool_terms:
        flags.append("fabricated_tooling")

    return flags
