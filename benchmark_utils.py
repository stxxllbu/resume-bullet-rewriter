"""
Utilities for V0 benchmark runs.

This module keeps benchmark logic in small functions to keep ``bench.py`` thin.
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from llm_ollama import OllamaRewriteError
from llm_openai import OpenAIRewriteError
from main import rewrite_with_backend

VALID_BACKENDS = {"rules", "openai", "ollama"}


def utc_now_iso() -> str:
    """Stable UTC timestamp string for logs and output metadata."""
    return datetime.now(timezone.utc).isoformat()


def load_bullets(path: str) -> list[str]:
    """Read one bullet per line; skip empty lines."""
    text = Path(path).read_text(encoding="utf-8")
    bullets: list[str] = []
    for line in text.splitlines():
        item = line.strip()
        if item:
            bullets.append(item)
    return bullets


def parse_backends(raw: str) -> list[str]:
    """Parse comma-separated backends and validate names."""
    backends = [x.strip() for x in raw.split(",") if x.strip()]
    if not backends:
        raise ValueError("No backends provided.")
    invalid = [x for x in backends if x not in VALID_BACKENDS]
    if invalid:
        raise ValueError(
            f"Unsupported backend(s): {', '.join(invalid)}. "
            f"Valid values: {', '.join(sorted(VALID_BACKENDS))}",
        )
    return backends


def compute_quality_flags(input_text: str, rewritten: str) -> dict[str, Any]:
    """Simple, explainable V0 heuristics for quick comparisons."""
    has_in_number = bool(re.search(r"\d", input_text))
    has_out_number = bool(re.search(r"\d", rewritten))
    return {
        "len_in": len(input_text.split()),
        "len_out": len(rewritten.split()),
        "added_number_flag": (not has_in_number) and has_out_number,
        "empty_output_flag": not bool(rewritten.strip()),
    }


def run_one(raw: str, backend: str, index: int) -> dict[str, Any]:
    """
    Run one rewrite on one backend and return a benchmark row.

    This function never raises backend errors; failures are captured into the row.
    """
    started = perf_counter()
    timestamp = utc_now_iso()
    try:
        result = rewrite_with_backend(raw, backend)
        latency_ms = (perf_counter() - started) * 1000.0
        return {
            "index": index,
            "backend": backend,
            "input": raw,
            "success": True,
            "rewritten": result.rewritten,
            "changes": result.changes,
            "latency_ms": latency_ms,
            "error_type": None,
            "error_message": None,
            "quality": compute_quality_flags(raw, result.rewritten),
            "timestamp": timestamp,
        }
    except (OpenAIRewriteError, OllamaRewriteError, ValueError) as e:
        latency_ms = (perf_counter() - started) * 1000.0
        return {
            "index": index,
            "backend": backend,
            "input": raw,
            "success": False,
            "rewritten": None,
            "changes": [],
            "latency_ms": latency_ms,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "quality": None,
            "timestamp": timestamp,
        }


def append_jsonl_line(path: Path, row: dict[str, Any]) -> None:
    """Append one JSON object line to a JSONL file."""
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _percentile(values: list[float], p: float) -> float:
    """Small percentile helper without extra dependencies."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (p / 100.0) * (len(ordered) - 1)
    low = int(math.floor(rank))
    high = int(math.ceil(rank))
    if low == high:
        return float(ordered[low])
    frac = rank - low
    return float(ordered[low] * (1.0 - frac) + ordered[high] * frac)


def summarize_results(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per-backend success and latency statistics."""
    by_backend: dict[str, dict[str, Any]] = {}

    for row in rows:
        backend = row["backend"]
        if backend not in by_backend:
            by_backend[backend] = {
                "total": 0,
                "success_count": 0,
                "fail_count": 0,
                "latencies_ms": [],
                "added_number_count": 0,
            }
        bucket = by_backend[backend]
        bucket["total"] += 1
        bucket["latencies_ms"].append(float(row["latency_ms"]))
        if row["success"]:
            bucket["success_count"] += 1
            quality = row.get("quality")
            if quality and quality.get("added_number_flag"):
                bucket["added_number_count"] += 1
        else:
            bucket["fail_count"] += 1

    summary_backends: dict[str, Any] = {}
    for backend, bucket in by_backend.items():
        total = bucket["total"]
        latencies = bucket["latencies_ms"]
        summary_backends[backend] = {
            "total": total,
            "success_count": bucket["success_count"],
            "fail_count": bucket["fail_count"],
            "success_rate": (bucket["success_count"] / total) if total else 0.0,
            "avg_latency_ms": (sum(latencies) / len(latencies)) if latencies else 0.0,
            "p95_latency_ms": _percentile(latencies, 95.0),
            "added_number_rate": (
                bucket["added_number_count"] / bucket["success_count"]
                if bucket["success_count"]
                else 0.0
            ),
        }

    return {
        "run_at": utc_now_iso(),
        "total_rows": len(rows),
        "by_backend": summary_backends,
    }


def write_json(path: Path, obj: dict[str, Any]) -> None:
    """Write a JSON object file with indentation."""
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
