"""
JD-aware 2-call rewrite pipeline using OpenAI Chat Completions.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict
from typing import Any, Dict, List, Tuple

from resume_rewriter.agent_jd_types import AgentJDArtifact, GapItem, JDRequirement, RewritePlanStep
from resume_rewriter.faithfulness_guard import run_faithfulness_guard
from resume_rewriter.rewriter import RewriteResult, normalize_whitespace

ANALYZE_PLAN_SYSTEM_PROMPT = (
    "You analyze one resume bullet against one job description. "
    "Return JSON only with keys: requirements, gaps, rewrite_plan. "
    "requirements must be a list of objects: {text, priority}. "
    "gaps must be a list of objects: {requirement, reason}. "
    "rewrite_plan must be a list of objects: {instruction}. "
    "Do not add markdown."
)

REWRITE_SYSTEM_PROMPT = (
    "You rewrite one resume bullet using a rewrite plan and requirements. "
    "Keep it faithful to the original bullet. "
    "Do not invent numbers, percentages, scale claims, or tools. "
    "Return JSON only with key: rewritten_bullet."
)


class AgentJDRewriteError(Exception):
    """Missing configuration, HTTP failure, or unexpected API response."""


def _chat_json(
    *,
    model: str,
    base: str,
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    timeout_s: float,
) -> Dict[str, Any]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    url = f"{base}/chat/completions"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise AgentJDRewriteError(f"HTTP {e.code}: {detail[:500]}") from e
    except urllib.error.URLError as e:
        raise AgentJDRewriteError(f"Request failed: {e.reason}") from e

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise AgentJDRewriteError(f"Unexpected API response shape: {data!r}") from e

    if not isinstance(content, str):
        raise AgentJDRewriteError("API returned non-string message content")

    text = content.strip()
    if not text:
        raise AgentJDRewriteError("Model returned empty content")

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise AgentJDRewriteError(f"Model did not return valid JSON: {text[:500]}") from e


def _parse_requirements(raw: Any) -> List[JDRequirement]:
    if not isinstance(raw, list):
        raise AgentJDRewriteError("Invalid requirements field: expected list")
    out: List[JDRequirement] = []
    for item in raw:
        if isinstance(item, str):
            text = normalize_whitespace(item)
            if text:
                out.append(JDRequirement(text=text, priority="must"))
            continue
        if isinstance(item, dict):
            text = normalize_whitespace(str(item.get("text", "")))
            if not text:
                continue
            priority = normalize_whitespace(str(item.get("priority", "must"))).lower()
            if priority not in {"must", "preferred"}:
                priority = "must"
            out.append(JDRequirement(text=text, priority=priority))
            continue
    return out


def _parse_gaps(raw: Any) -> List[GapItem]:
    if not isinstance(raw, list):
        raise AgentJDRewriteError("Invalid gaps field: expected list")
    out: List[GapItem] = []
    for item in raw:
        if isinstance(item, str):
            text = normalize_whitespace(item)
            if text:
                out.append(GapItem(requirement=text, reason="missing detail"))
            continue
        if isinstance(item, dict):
            requirement = normalize_whitespace(str(item.get("requirement", "")))
            reason = normalize_whitespace(str(item.get("reason", "")))
            if requirement:
                out.append(GapItem(requirement=requirement, reason=reason or "missing detail"))
            continue
    return out


def _parse_rewrite_plan(raw: Any) -> List[RewritePlanStep]:
    if not isinstance(raw, list):
        raise AgentJDRewriteError("Invalid rewrite_plan field: expected list")
    out: List[RewritePlanStep] = []
    for item in raw:
        if isinstance(item, str):
            instruction = normalize_whitespace(item)
            if instruction:
                out.append(RewritePlanStep(instruction=instruction))
            continue
        if isinstance(item, dict):
            instruction = normalize_whitespace(str(item.get("instruction", "")))
            if instruction:
                out.append(RewritePlanStep(instruction=instruction))
            continue
    return out


def _call_analyze_plan(
    raw: str,
    jd_text: str,
    *,
    model: str,
    base: str,
    api_key: str,
    timeout_s: float,
) -> Tuple[List[JDRequirement], List[GapItem], List[RewritePlanStep]]:
    user_prompt = (
        "Bullet:\n"
        f"{raw}\n\n"
        "Job Description:\n"
        f"{jd_text}\n"
    )
    data = _chat_json(
        model=model,
        base=base,
        api_key=api_key,
        system_prompt=ANALYZE_PLAN_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        timeout_s=timeout_s,
    )
    requirements = _parse_requirements(data.get("requirements"))
    gaps = _parse_gaps(data.get("gaps"))
    rewrite_plan = _parse_rewrite_plan(data.get("rewrite_plan"))
    if not rewrite_plan:
        raise AgentJDRewriteError("Analyze-plan response did not include a usable rewrite_plan")
    return requirements, gaps, rewrite_plan


def _call_rewrite(
    raw: str,
    rewrite_plan: List[RewritePlanStep],
    requirements: List[JDRequirement],
    gaps: List[GapItem],
    *,
    model: str,
    base: str,
    api_key: str,
    timeout_s: float,
) -> str:
    plan_lines = "\n".join(f"- {step.instruction}" for step in rewrite_plan) or "- Keep factual wording."
    req_lines = "\n".join(f"- [{r.priority}] {r.text}" for r in requirements) or "- (none)"
    gap_lines = "\n".join(f"- {g.requirement}: {g.reason}" for g in gaps) or "- (none)"
    user_prompt = (
        "Original Bullet:\n"
        f"{raw}\n\n"
        "Requirements:\n"
        f"{req_lines}\n\n"
        "Detected Gaps:\n"
        f"{gap_lines}\n\n"
        "Rewrite Plan:\n"
        f"{plan_lines}\n"
    )
    data = _chat_json(
        model=model,
        base=base,
        api_key=api_key,
        system_prompt=REWRITE_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        timeout_s=timeout_s,
    )
    rewritten = normalize_whitespace(str(data.get("rewritten_bullet", "")))
    if not rewritten:
        raise AgentJDRewriteError("Rewrite response did not include rewritten_bullet")
    return rewritten


def run_agent_jd_pipeline(raw: str, jd_text: str, *, timeout_s: float = 60.0) -> AgentJDArtifact:
    """
    Two-call pipeline:
    1) analyze + plan
    2) rewrite using raw + rewrite_plan + requirements
    """
    original = normalize_whitespace(raw)
    jd_clean = normalize_whitespace(jd_text)
    if not original:
        raise AgentJDRewriteError("Input bullet is empty.")
    if not jd_clean:
        raise AgentJDRewriteError("JD text is empty. Provide a non-empty --jd-file.")

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise AgentJDRewriteError("OPENAI_API_KEY is not set.")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()
    base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")

    requirements, gaps, rewrite_plan = _call_analyze_plan(
        original,
        jd_clean,
        model=model,
        base=base,
        api_key=api_key,
        timeout_s=timeout_s,
    )
    rewritten = _call_rewrite(
        original,
        rewrite_plan,
        requirements,
        gaps,
        model=model,
        base=base,
        api_key=api_key,
        timeout_s=timeout_s,
    )
    risk_flags = run_faithfulness_guard(original, rewritten)

    return AgentJDArtifact(
        original=original,
        jd_text=jd_clean,
        requirements=requirements,
        gaps=gaps,
        rewrite_plan=rewrite_plan,
        rewritten_bullet=rewritten,
        risk_flags=risk_flags,
    )


def rewrite_with_agent_jd(raw: str, jd_text: str, *, timeout_s: float = 60.0) -> RewriteResult:
    """Run the pipeline and convert artifact into existing RewriteResult shape."""
    artifact = run_agent_jd_pipeline(raw, jd_text, timeout_s=timeout_s)
    if not artifact.original and "(empty input: skipped)" in artifact.risk_flags:
        return RewriteResult(original="", rewritten="", changes=["(empty input: skipped)"])

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()
    changes = [f"Agent JD rewrite ({model})", "2-step pipeline: analyze_plan -> rewrite"]
    if artifact.risk_flags:
        changes.extend(f"risk_flag: {flag}" for flag in artifact.risk_flags)
    else:
        changes.append("risk_flag: (none)")

    return RewriteResult(
        original=artifact.original,
        rewritten=artifact.rewritten_bullet,
        changes=changes,
    )


def artifact_to_json_dict(artifact: AgentJDArtifact) -> dict[str, object]:
    """Convert artifact dataclass tree into a JSON-serializable dictionary."""
    return asdict(artifact)

