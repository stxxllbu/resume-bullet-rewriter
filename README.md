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
python main.py -f bullets.txt
```

**Stdin** (use `-` instead of a path):

```bash
cat bullets.txt | python main.py --file -
printf '%s\n' "worked on the API" | python main.py -f -
```

## Output

For each bullet:

- **Original Bullet**
- **Rewritten Bullet**
- **Changes** (which rules fired, or a note when none matched)

File mode prints a `---` separator between bullets.

## Optional: OpenAI API smoke test (`scripts/`)

The main CLI above is **rules-only** (no network). To **manually verify** your OpenAI API key and see a raw `chat/completions` JSON response, use the helper script:

```bash
export OPENAI_API_KEY='sk-...'   # never commit real keys
./scripts/openai_resume_smoke.sh
./scripts/openai_resume_smoke.sh "Was part of the release rotation"
```

- **First argument** (optional): the resume bullet text to send as the `user` message. If omitted, a default example bullet is used.
- **Environment variables** (optional):
  - `OPENAI_MODEL` — defaults to `gpt-4o-mini`
  - `OPENAI_API_BASE` — defaults to `https://api.openai.com/v1` (any OpenAI-compatible base URL)

The script builds JSON with **Python** (`json.dumps`) so bullets with quotes or special characters are safe; it does **not** embed your API key in the file—only reads `OPENAI_API_KEY` from the environment.

## Design

- **`rules.py`** — patterns and replacements only (no logic).
- **`rewriter.py`** — applies rules in a fixed order; returns a `RewriteResult` dataclass.
- **`main.py`** — CLI and printing.
- **`scripts/openai_resume_smoke.sh`** — optional local curl + Python JSON helper for OpenAI (not used by `main.py`).

Rules are **deterministic**: same input → same output. They **do not** add numbers, percentages, or business-impact claims.
