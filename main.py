#!/usr/bin/env python3
"""
V1 CLI: rule-based resume bullet rewriter (no API).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

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


def run_bullet(text: str) -> None:
    """Rewrite and print one bullet."""
    print(format_output(rewrite(text)))
    print()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rewrite resume bullets with conservative rules (V1, no API).",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        metavar="PATH",
        help="Text file with one bullet per line (empty lines skipped).",
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

    if args.file is not None:
        path = args.file
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
            run_bullet(raw)
            first = False
        return

    run_bullet(args.bullet)


if __name__ == "__main__":
    main()
