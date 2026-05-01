#!/usr/bin/env python3
"""
CLI: resume bullet rewriter with a unified --backend selector.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from llm_agent_jd import (
    AgentJDRewriteError,
    artifact_to_json_dict,
    rewrite_with_agent_jd,
    run_agent_jd_pipeline,
)
from llm_ollama import OllamaRewriteError, rewrite_with_ollama
from llm_openai import OpenAIRewriteError, rewrite_with_openai
from rewriter import RewriteResult, rewrite


def format_output(result: RewriteResult) -> str:
    """Readable, deterministic sections for one bullet."""
    lines = [
        "Original Bullet:",
        result.original,
        "",
        "Rewritten Bullet:",
        result.rewritten,
        "",
        "Changes:",
    ]
    if result.changes:
        lines.extend(f"- {c}" for c in result.changes)
    else:
        lines.append("- (none)")
    return "\n".join(lines)


def rewrite_with_backend(raw: str, backend: str, jd_text: str | None = None) -> RewriteResult:
    """Dispatch one rewrite request to the selected backend."""
    if backend == "rules":
        return rewrite(raw)
    if backend == "openai":
        return rewrite_with_openai(raw)
    if backend == "ollama":
        return rewrite_with_ollama(raw)
    if backend == "agent_jd":
        if jd_text is None:
            raise ValueError("agent_jd requires --jd-file")
        return rewrite_with_agent_jd(raw, jd_text)
    raise ValueError(f"Unsupported backend: {backend}")


def run_one(text: str, backend: str, jd_text: str | None = None, json_output: bool = False) -> None:
    """Rewrite and print one text input."""
    if backend == "agent_jd" and json_output:
        if jd_text is None:
            raise ValueError("agent_jd requires --jd-file")
        artifact = run_agent_jd_pipeline(text, jd_text)
        print(json.dumps(artifact_to_json_dict(artifact), ensure_ascii=False, indent=2))
        print("")
        return

    result = rewrite_with_backend(text, backend, jd_text=jd_text)
    print(format_output(result))
    print("")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rewrite resume bullets with a selectable backend.",
    )
    parser.add_argument(
        "--backend",
        choices=["rules", "openai", "ollama", "agent_jd"],
        default="rules",
        help=(
            "Rewrite backend: rules (local rule-based rewrite), "
            "openai (OpenAI API), ollama (local Ollama), "
            "agent_jd (JD-aware 2-step pipeline)."
        ),
    )
    parser.add_argument(
        "--jd-file",
        help="Job description text file. Required when --backend agent_jd.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="With --backend agent_jd, print full pipeline artifact JSON.",
    )
    parser.add_argument(
        "-f",
        "--file",
        help='Text file with one bullet per line (empty lines skipped). Use "-" for stdin.',
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Single text input as one argument (quote if it contains spaces).",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args(sys.argv[1:])

    if args.file is None and args.text is None:
        print("Error: provide either --file PATH or a bullet string.", file=sys.stderr)
        sys.exit(2)
    if args.file is not None and args.text is not None:
        print("Error: use either --file or a bullet string, not both.", file=sys.stderr)
        sys.exit(2)
    backend = args.backend
    jd_text: str | None = None
    if backend == "agent_jd":
        if not args.jd_file:
            print("Error: --jd-file is required when --backend agent_jd.", file=sys.stderr)
            sys.exit(2)
        jd_path = Path(args.jd_file)
        if not jd_path.is_file():
            print(f"Error: not a file: {jd_path}", file=sys.stderr)
            sys.exit(1)
        jd_text = jd_path.read_text(encoding="utf-8")

    try:
        if args.file is not None:
            if args.file == "-":
                text = sys.stdin.read()
            else:
                path = Path(args.file)
                if not path.is_file():
                    print(f"Error: not a file: {path}", file=sys.stderr)
                    sys.exit(1)
                text = path.read_text(encoding="utf-8")
            first = True
            for line in text.splitlines():
                raw = line.strip()
                if not raw:
                    continue
                if not first:
                    print("---")
                    print()
                run_one(raw, backend, jd_text=jd_text, json_output=args.json)
                first = False
            return

        run_one(args.text, backend, jd_text=jd_text, json_output=args.json)
    except (OpenAIRewriteError, OllamaRewriteError, AgentJDRewriteError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
