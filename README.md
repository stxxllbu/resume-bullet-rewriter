# resume-bullet-rewriter

CLI that rewrites resume bullets.

- **Default (no flag):** **rule-based** swaps only—**no API keys, no network**, no invented metrics.
- **`--backend openai`:** calls **OpenAI** Chat Completions (`llm_openai.py`). Requires `OPENAI_API_KEY` and network. **No fallback to rules:** if the key is missing or the request fails, the CLI prints an error and exits non-zero.
- **`--backend ollama`:** calls **local Ollama** `/api/chat` (`llm_ollama.py`). Requires the **Ollama service** running (e.g. `ollama serve` or systemd) and the model pulled (default `qwen2.5:7b`). No fallback to rules on failure.
- **`--backend agent_jd`:** calls a **2-step OpenAI pipeline** (`llm_agent_jd.py`) that analyzes bullet+JD, plans rewrite, rewrites, then applies `faithfulness_guard.py`. Requires `OPENAI_API_KEY` and `--jd-file`.

## Requirements

- Python **3.10+**
- **Runtime:** no third-party pip packages (stdlib + this repo only; see `dependencies = []` in `pyproject.toml`).
- **Development:** `pytest` via optional extra `[dev]` in `pyproject.toml`.

## Setup

```bash
cd resume-bullet-rewriter
python3 -m venv .venv          # use Python 3.10+ (e.g. python3.12 -m venv .venv)
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"        # editable install + pytest + CLI entry points
```

After install:

- **`resume-rewrite`** — same flags as `python main.py` (e.g. `resume-rewrite --backend rules "..."`)
- **`resume-bench`** — same as `python bench.py`
- **`pytest`** — run the test suite

`python main.py` and `python bench.py` still work without installing.

## Tests

```bash
pytest
# or: python -m pytest tests/ -v
```

(Requires `pip install -e ".[dev]"` from Setup above.)

- **`tests/test_rewriter.py`** — rule engine: whitespace, empty input, phrase/leading rules, no-match normalization, idempotency.
- **`tests/test_llm_openai.py`** — OpenAI client with **mocked** `urllib` (no network, no real key). Covers missing key, success parsing, HTTP errors, bad JSON shape, non-string `content`.
- **`tests/test_llm_ollama.py`** — Ollama client with **mocked** `urllib` (no Ollama process). Covers empty input, success parsing, HTTP / URL errors, bad JSON shape, non-string `content`.

## Usage

**Single bullet** (quote if it contains spaces):

```bash
python main.py "helped with onboarding documentation"
python main.py --backend rules "helped with onboarding documentation"
python main.py --backend openai "worked on the internal API"
python main.py --backend ollama "worked on the internal API"
python main.py --backend agent_jd --jd-file data/jd_ml_platform.txt "worked on improving training pipeline reliability"
```

**OpenAI rewrite** (same input shapes as above; set `--backend openai`):

```bash
export OPENAI_API_KEY='sk-...'   # never commit real keys
python main.py --backend openai "worked on the internal API"
python main.py --backend openai -f bullets.txt
```

Optional environment variables (same defaults as `scripts/openai_resume_smoke.sh`):

- `OPENAI_MODEL` — default `gpt-4o-mini`
- `OPENAI_API_BASE` — default `https://api.openai.com/v1` (OpenAI-compatible endpoints)

**Agent JD rewrite** (JD-aware; requires `--jd-file`):

```bash
export OPENAI_API_KEY='sk-...'   # never commit real keys
python main.py --backend agent_jd --jd-file data/jd_ml_platform.txt "worked on improving training pipeline reliability"

# print full intermediate artifact JSON (requirements/gaps/plan/risk_flags)
python main.py --backend agent_jd --jd-file data/jd_ml_platform.txt --json "worked on improving training pipeline reliability"
```

Sample JD file is provided at `data/jd_ml_platform.txt`.

**Ollama rewrite** (local HTTP; set `--backend ollama`; same input shapes as OpenAI):

```bash
# Ollama must be running; model must exist locally, e.g. ollama pull qwen2.5:7b
python main.py --backend ollama "worked on the internal API"
python main.py --backend ollama -f bullets.txt
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

## Benchmark (V0)

Run one dataset across multiple backends and collect comparable results.

```bash
# one bullet per line
python bench.py --input data/bullets.txt

# select backends explicitly
python bench.py --input data/bullets.txt --backends rules,openai,ollama

# optional controls
python bench.py --input data/bullets.txt --max-samples 100 --verbose
```

Outputs are saved under `benchmark_runs/<timestamp>/` by default:

- `results.jsonl` — one row per `(input, backend)` run
- `summary.json` — aggregated success/latency metrics per backend
- `meta.json` — run configuration metadata

## Output

For each bullet:

- **Original Bullet**
- **Rewritten Bullet**
- **Changes** — with rules: which rules fired (or a note when none matched). With `--backend openai`: a line such as `OpenAI rewrite (<model>)`. With `--backend ollama`: `Ollama rewrite (<model>)`.

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
- **`llm_openai.py`** — OpenAI HTTPS client + prompt; returns `RewriteResult` for `--backend openai`.
- **`llm_ollama.py`** — Ollama `/api/chat` client + same prompt as OpenAI; returns `RewriteResult` for `--backend ollama`.
- **`agent_jd_types.py`** — dataclasses for JD-aware rewrite artifacts.
- **`faithfulness_guard.py`** — rule-based risk flags for potentially unsupported claims.
- **`llm_agent_jd.py`** — 2-step OpenAI pipeline for `--backend agent_jd`; returns both artifact and `RewriteResult`-compatible output.
- **`main.py`** — CLI and printing (`--backend rules|openai|ollama|agent_jd`, `--jd-file`, `--json`); entry point `resume-rewrite`.
- **`pyproject.toml`** — packaging, `requires-python`, dev deps, and console scripts.
- **`benchmark_utils.py`** — helper functions for V0 benchmarking (load/run/summarize/write).
- **`bench.py`** — benchmark runner CLI for multi-backend comparisons.
- **`scripts/openai_resume_smoke.sh`** — optional curl + Python JSON helper (raw API response).

Rules are **deterministic**: same input → same output. They **do not** add numbers, percentages, or business-impact claims. **`--backend openai` and `--backend ollama` output are not deterministic** (sampling / model-dependent).
