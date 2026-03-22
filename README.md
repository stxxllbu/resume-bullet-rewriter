# resume-bullet-rewriter

V0: a tiny **rule-based** CLI that rewrites one resume bullet (no API keys, no network).

## Requirements

- Python **3.10+** recommended (uses `list[str]` type hints; 3.9+ works if you adjust hints).

## Setup (optional)

```bash
cd resume-bullet-rewriter
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

There are no third-party dependencies in V0; `pip install -r requirements.txt` is optional and should do nothing beyond satisfying the file.

## Run

```bash
python main.py "Built a model for ad prediction"
```

Example output:

```text
Rewritten bullet:
Developed a predictive modeling pipeline for ad targeting, improving signal quality and enabling more reliable performance analysis.
```

## Notes

- **V0** uses small string rules in `main.py`. Swap in an LLM or richer logic later if you want.
- Pass the bullet in **one quoted argument** so spaces stay in a single string.
