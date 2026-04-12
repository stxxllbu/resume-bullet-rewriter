"""
Ollama /api/chat client for resume bullet rewrite (HTTP; no rule engine).
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


class OllamaRewriteError(Exception):
    """Missing configuration, HTTP failure, or unexpected API response."""


def rewrite_with_ollama(raw: str, *, timeout_s: float = 60.0) -> RewriteResult:
    """
    POST /api/chat; return RewriteResult for the same CLI shape as rules / OpenAI.
    """
    original = normalize_whitespace(raw)
    if not original:
        return RewriteResult(original="", rewritten="", changes=["(empty input: skipped)"])

    base = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").strip().rstrip("/")
    model = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b").strip()

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Rewrite this bullet:\n\n{original}"},
        ],
        "stream": False,
    }

    url = f"{base}/api/chat"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise OllamaRewriteError(f"HTTP {e.code}: {detail[:500]}") from e
    except urllib.error.URLError as e:
        raise OllamaRewriteError(f"Request failed: {e.reason}") from e

    try:
        content = data["message"]["content"]
    except (KeyError, TypeError) as e:
        raise OllamaRewriteError(f"Unexpected API response shape: {data!r}") from e

    if not isinstance(content, str):
        raise OllamaRewriteError("API returned non-string message content")

    rewritten = ""
    for line in content.splitlines():
        stripped = normalize_whitespace(line)
        if stripped:
            rewritten = stripped
            break

    changes = [f"Ollama rewrite ({model})"]
    return RewriteResult(original=original, rewritten=rewritten, changes=changes)
