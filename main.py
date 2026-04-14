#!/usr/bin/env python3
"""
CLI: resume bullet rewriter with a unified --backend selector.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

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


def rewrite_with_backend(raw: str, backend: str) -> RewriteResult:
    """Dispatch one rewrite request to the selected backend."""
    if backend == "rules":
        return rewrite(raw)
    if backend == "openai":
        return rewrite_with_openai(raw)
    if backend == "ollama":
        return rewrite_with_ollama(raw)
    raise ValueError(f"Unsupported backend: {backend}")


def run_bullet(text: str, backend: str) -> None:
    """Rewrite and print one bullet."""
    result = rewrite_with_backend(text, backend)
    print(format_output(result))
    print()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rewrite resume bullets with a selectable backend.",
    )
    parser.add_argument(
        "--backend",
        choices=["rules", "openai", "ollama"],
        default="rules",
        help=(
            "Rewrite backend: rules (local rule-based rewrite), "
            "openai (OpenAI API), ollama (local Ollama)."
        ),
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        metavar="PATH",
        help='Text file with one bullet per line (empty lines skipped). Use "-" for stdin.',
    )
    parser.add_argument(
        "bullet",
        nargs="?",
        help="Single bullet as one argument (quote if it contains spaces).",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args(sys.argv[1:])

    if args.file is None and args.bullet is None:
        print("Error: provide either --file PATH or a bullet string.", file=sys.stderr)
        sys.exit(2)
    if args.file is not None and args.bullet is not None:
        print("Error: use either --file or a bullet string, not both.", file=sys.stderr)
        sys.exit(2)
    backend = args.backend

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
                run_bullet(raw, backend)
                first = False
            return

        run_bullet(args.bullet, backend)
    except (OpenAIRewriteError, OllamaRewriteError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
