# resume-bullet-rewriter

CLI that rewrites resume bullets.

- **Default (no flag):** **rule-based** swaps only—**no API keys, no network**, no invented metrics.
- **`--llm`:** calls **OpenAI** Chat Completions (`llm_openai.py`). Requires `OPENAI_API_KEY` and network. **No fallback to rules:** if the key is missing or the request fails, the CLI prints an error and exits non-zero.
- **`--ollama`:** calls **local Ollama** `/api/chat` (`llm_ollama.py`). Requires the **Ollama service** running (e.g. `ollama serve` or systemd) and the model pulled (default `qwen2.5:7b`). **Use `--llm` or `--ollama`, not both.** No fallback to rules on failure.

## Requirements

- Python **3.10+** (stdlib only; see `requirements.txt`).

## Setup (optional)

```bash
cd resume-bullet-rewriter
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Tests (development)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

- **`tests/test_rewriter.py`** — rule engine: whitespace, empty input, phrase/leading rules, no-match normalization, idempotency.
- **`tests/test_llm_openai.py`** — OpenAI client with **mocked** `urllib` (no network, no real key). Covers missing key, success parsing, HTTP errors, bad JSON shape, non-string `content`.
- **`tests/test_llm_ollama.py`** — Ollama client with **mocked** `urllib` (no Ollama process). Covers empty input, success parsing, HTTP / URL errors, bad JSON shape, non-string `content`.

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

**Ollama rewrite** (local HTTP; add `--ollama`; same input shapes as OpenAI):

```bash
# Ollama must be running; model must exist locally, e.g. ollama pull qwen2.5:7b
python main.py --ollama "worked on the internal API"
python main.py --ollama -f bullets.txt
```

Optional environment variables:

- `OLLAMA_HOST` — default `http://127.0.0.1:11434`
- `OLLAMA_MODEL` — default `qwen2.5:7b`

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
- **Changes** — with rules: which rules fired (or a note when none matched). With `--llm`: a line such as `OpenAI rewrite (<model>)`. With `--ollama`: `Ollama rewrite (<model>)`.

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
- **`llm_ollama.py`** — Ollama `/api/chat` client + same prompt as OpenAI; returns `RewriteResult` for `--ollama`.
- **`main.py`** — CLI and printing (`--llm` / `--ollama` vs default rules).
- **`scripts/openai_resume_smoke.sh`** — optional curl + Python JSON helper (raw API response).

Rules are **deterministic**: same input → same output. They **do not** add numbers, percentages, or business-impact claims. **`--llm` and `--ollama` output are not deterministic** (sampling / model-dependent).
