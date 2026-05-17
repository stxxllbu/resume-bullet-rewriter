"""
Dataclasses for JD-aware rewrite artifacts.

This module intentionally contains only data structures (no business logic).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class JDRequirement:
    """One extracted JD requirement with an optional priority label."""

    text: str
    priority: str = "must"


@dataclass(frozen=True)
class GapItem:
    """One mismatch between bullet evidence and JD requirement."""

    requirement: str
    reason: str


@dataclass(frozen=True)
class RewritePlanStep:
    """One rewrite instruction derived from gap analysis."""

    instruction: str


@dataclass(frozen=True)
class AgentJDArtifact:
    """Full pipeline artifact for inspectable JD-aware rewriting."""

    original: str
    jd_text: str
    requirements: List[JDRequirement] = field(default_factory=list)
    gaps: List[GapItem] = field(default_factory=list)
    rewrite_plan: List[RewritePlanStep] = field(default_factory=list)
    rewritten_bullet: str = ""
    risk_flags: List[str] = field(default_factory=list)
