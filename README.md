# resume-bullet-rewriter

CLI that rewrites resume bullets.

- **Default (no flag):** **rule-based** swaps only—**no API keys, no network**, no invented metrics.
- **`--llm`:** calls **OpenAI** Chat Completions (`llm_openai.py`). Requires `OPENAI_API_KEY` and network. **No fallback to rules:** if the key is missing or the request fails, the CLI prints an error and exits non-zero.

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

**OpenAI rewrite** (same input shapes as above; add `--llm`):

```bash
export OPENAI_API_KEY='sk-...'   # never commit real keys
python main.py --llm "worked on the internal API"
python main.py --llm -f bullets.txt
```

Optional environment variables (same defaults as `scripts/openai_resume_smoke.sh`):

- `OPENAI_MODEL` — default `gpt-4o-mini`
- `OPENAI_API_BASE` — default `https://api.openai.com/v1` (OpenAI-compatible endpoints)

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
- **Changes** — with rules: which rules fired (or a note when none matched). With `--llm`: a line such as `OpenAI rewrite (<model>)`.

File mode prints a `---` separator between bullets.

## Optional: OpenAI API smoke test (`scripts/`)

To **manually verify** your key and inspect a **raw** `chat/completions` JSON response (without the formatted CLI sections above), use:

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
- **`llm_openai.py`** — OpenAI HTTPS client + prompt; returns `RewriteResult` for `--llm`.
- **`main.py`** — CLI and printing (`--llm` toggles OpenAI vs rules).
- **`scripts/openai_resume_smoke.sh`** — optional curl + Python JSON helper (raw API response).

Rules are **deterministic**: same input → same output. They **do not** add numbers, percentages, or business-impact claims. **`--llm` output is not deterministic** (model-dependent).
