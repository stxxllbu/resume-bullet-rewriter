#!/usr/bin/env python3
"""
CLI: rule-based resume bullet rewriter; optional --llm via OpenAI.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

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


def run_bullet(text: str, *, use_openai: bool) -> None:
    """Rewrite and print one bullet."""
    if use_openai:
        result = rewrite_with_openai(text)
    else:
        result = rewrite(text)
    print(format_output(result))
    print()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rewrite resume bullets: default rules (local), or --llm (OpenAI API).",
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Use OpenAI Chat Completions (needs OPENAI_API_KEY and network).",
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

    use_openai = args.llm

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
            try:
                run_bullet(raw, use_openai=use_openai)
            except OpenAIRewriteError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
            first = False
        return

    try:
        run_bullet(args.bullet, use_openai=use_openai)
    except OpenAIRewriteError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
