"""
OpenAI Chat Completions client for resume bullet rewrite (HTTPS only; no rule engine).
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from rewriter import RewriteResult, normalize_whitespace

SYSTEM_PROMPT = (
    "Rewrite resume bullets. Do not add numbers or metrics not in the original. "
    "Output one line only."
)


class OpenAIRewriteError(Exception):
    """Missing configuration, HTTP failure, or unexpected API response."""


def rewrite_with_openai(raw: str, *, timeout_s: float = 60.0) -> RewriteResult:
    """
    POST /v1/chat/completions; return RewriteResult for the same CLI shape as rules.
    """
    original = normalize_whitespace(raw)
    if not original:
        return RewriteResult(original="", rewritten="", changes=["(empty input: skipped)"])

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise OpenAIRewriteError(
            "OPENAI_API_KEY is not set. Export it before using --llm.",
        )

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()
    base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Rewrite this bullet:\n\n{original}"},
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
        raise OpenAIRewriteError(f"HTTP {e.code}: {detail[:500]}") from e
    except urllib.error.URLError as e:
        raise OpenAIRewriteError(f"Request failed: {e.reason}") from e

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise OpenAIRewriteError(f"Unexpected API response shape: {data!r}") from e

    if not isinstance(content, str):
        raise OpenAIRewriteError("API returned non-string message content")

    rewritten = ""
    for line in content.splitlines():
        stripped = normalize_whitespace(line)
        if stripped:
            rewritten = stripped
            break

    changes = [f"OpenAI rewrite ({model})"]
    return RewriteResult(original=original, rewritten=rewritten, changes=changes)
