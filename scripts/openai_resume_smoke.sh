#!/usr/bin/env bash
# Local smoke test: one Chat Completions call for resume-bullet rewrite.
#
# Usage:
#   export OPENAI_API_KEY='sk-...'
#   ./scripts/openai_resume_smoke.sh
#   ./scripts/openai_resume_smoke.sh "your bullet text here"
#
# Optional:
#   OPENAI_MODEL=gpt-4o-mini (default)
#   OPENAI_API_BASE=https://api.openai.com/v1 (default)
#
# Do not put your API key inside this file. Do not commit keys.

set -euo pipefail

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "Error: set OPENAI_API_KEY first, e.g. export OPENAI_API_KEY='sk-...'" >&2
  exit 1
fi

BULLET="${1:-worked on the internal API}"
MODEL="${OPENAI_MODEL:-gpt-4o-mini}"
BASE="${OPENAI_API_BASE:-https://api.openai.com/v1}"
BASE="${BASE%/}"

export BULLET MODEL

JSON="$(
  python3 -c '
import json, os
bullet = os.environ["BULLET"]
model = os.environ["MODEL"]
print(
    json.dumps(
        {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Rewrite resume bullets. Do not add numbers or metrics "
                        "not in the original. Output one line only."
                    ),
                },
                {
                    "role": "user",
                    "content": "Rewrite this bullet:\n\n" + bullet,
                },
            ],
        }
    )
)
'
)"

curl -sS "${BASE}/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -d "${JSON}"

echo
