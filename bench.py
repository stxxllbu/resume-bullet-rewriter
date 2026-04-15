#!/usr/bin/env python3
"""
V0 benchmark runner for resume-bullet-rewriter backends.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from benchmark_utils import (
    append_jsonl_line,
    load_bullets,
    parse_backends,
    run_one,
    summarize_results,
    utc_now_iso,
    write_json,
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run benchmark across rules/openai/ollama backends.",
    )
    parser.add_argument("--input", required=True, help="Input text file: one bullet per line.")
    parser.add_argument(
        "--backends",
        default="rules,openai,ollama",
        help="Comma-separated backends. Default: rules,openai,ollama",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Output directory. Default: benchmark_runs/<UTC timestamp>",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Optional cap on number of bullets from input.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop immediately on first backend failure.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-row progress while running.",
    )
    return parser.parse_args(argv)


def _default_out_dir() -> Path:
    # Keep path-safe timestamp by replacing ":".
    ts = utc_now_iso().replace(":", "-")
    return Path("benchmark_runs") / ts


def _print_summary(summary: dict[str, Any]) -> None:
    print("Benchmark summary:")
    for backend, s in summary["by_backend"].items():
        print(
            f"- {backend}: success_rate={s['success_rate']:.2%}, "
            f"avg_latency_ms={s['avg_latency_ms']:.1f}, "
            f"p95_latency_ms={s['p95_latency_ms']:.1f}, "
            f"n={s['total']}",
        )


def main() -> None:
    args = parse_args(sys.argv[1:])
    backends = parse_backends(args.backends)
    bullets = load_bullets(args.input)
    if args.max_samples is not None:
        bullets = bullets[: args.max_samples]

    out_dir = Path(args.out_dir) if args.out_dir else _default_out_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "results.jsonl"
    summary_path = out_dir / "summary.json"
    meta_path = out_dir / "meta.json"

    rows: list[dict[str, Any]] = []
    # Start fresh for the run.
    results_path.write_text("", encoding="utf-8")

    for i, bullet in enumerate(bullets):
        for backend in backends:
            row = run_one(bullet, backend, i)
            rows.append(row)
            append_jsonl_line(results_path, row)

            if args.verbose:
                status = "ok" if row["success"] else "error"
                print(
                    f"[{status}] i={i} backend={backend} "
                    f"latency_ms={row['latency_ms']:.1f}",
                )

            if args.fail_fast and not row["success"]:
                print("Fail-fast enabled: stopping on first failure.", file=sys.stderr)
                summary = summarize_results(rows)
                write_json(summary_path, summary)
                write_json(
                    meta_path,
                    {
                        "input": args.input,
                        "backends": backends,
                        "max_samples": args.max_samples,
                        "fail_fast": True,
                        "stopped_early": True,
                        "rows_written": len(rows),
                    },
                )
                _print_summary(summary)
                return

    summary = summarize_results(rows)
    write_json(summary_path, summary)
    write_json(
        meta_path,
        {
            "input": args.input,
            "backends": backends,
            "max_samples": args.max_samples,
            "fail_fast": bool(args.fail_fast),
            "stopped_early": False,
            "rows_written": len(rows),
        },
    )
    _print_summary(summary)
    print(f"Saved: {results_path}")
    print(f"Saved: {summary_path}")


if __name__ == "__main__":
    main()
