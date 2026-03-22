# resume-bullet-rewriter

V1: a **rule-based** CLI that rewrites resume bullets with **conservative** verb/phrasing swaps. **No API keys, no network, no invented metrics.**

## Requirements

- Python **3.10+** (stdlib only; see `requirements.txt`).

## Setup (optional)

```bash
cd resume-bullet-rewriter
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

**Single bullet** (quote if it contains spaces):

```bash
python main.py "helped with onboarding documentation"
```

**Many bullets** (one per line; empty lines are skipped):

```bash
python main.py --file bullets.txt
# short form:
python main.py -f bullets.txt
```

## Output

For each bullet:

- **Original Bullet**
- **Rewritten Bullet**
- **Changes** (which rules fired, or a note when none matched)

File mode prints a `---` separator between bullets.

## Design

- **`rules.py`** — patterns and replacements only (no logic).
- **`rewriter.py`** — applies rules in a fixed order; returns a `RewriteResult` dataclass.
- **`main.py`** — CLI and printing.

Rules are **deterministic**: same input → same output. They **do not** add numbers, percentages, or business-impact claims.
