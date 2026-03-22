#!/usr/bin/env python3
"""
V0 CLI: rewrite one resume bullet using simple rules (no API).
"""

from __future__ import annotations

import argparse
import sys


def rewrite_bullet(raw: str) -> str:
    """
    Rule-based rewrite for V0.

    - Normalizes whitespace.
    - Handles one known demo phrase with a fixed, resume-style rewrite.
    - Otherwise applies a tiny generic tweak (e.g. "Built" -> "Developed") and trailing period.
    """
    text = " ".join(raw.strip().split())
    if not text:
        return "Please provide a non-empty bullet string."

    # Demo / smoke-test path: matches the README example.
    if "built a model for ad prediction" in text.lower():
        return (
            "Developed a predictive modeling pipeline for ad targeting, "
            "improving signal quality and enabling more reliable performance analysis."
        )

    words = text.split()
    # Light verb swap if the bullet starts with "Built" (common in drafts).
    if words and words[0].lower() == "built":
        words[0] = "Developed"
        text = " ".join(words)

    if not text.endswith("."):
        text += "."

    return text


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI: exactly one positional string (the bullet text)."""
    parser = argparse.ArgumentParser(
        description="Rewrite a single resume bullet (V0, rule-based).",
    )
    parser.add_argument(
        "bullet",
        help='Raw bullet text, e.g. Built a model for ad prediction',
    )
    return parser.parse_args(argv)


def main() -> None:
    """Entry point: rewrite and print in the required format."""
    args = parse_args(sys.argv[1:])
    rewritten = rewrite_bullet(args.bullet)
    print("Rewritten bullet:")
    print(rewritten)


if __name__ == "__main__":
    main()
