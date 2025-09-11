#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="python3"
INPUT_JSON="raw_miro_data.json"
OUTPUT_MMD="GPT_raw_to_mermaid.mmd"
PY_SCRIPT="GPT_raw_to_mermaid.py"

if [[ ! -f "$PY_SCRIPT" ]]; then
  echo "Error: $PY_SCRIPT not found" >&2
  exit 1
fi
if [[ ! -f "$INPUT_JSON" ]]; then
  echo "Error: $INPUT_JSON not found" >&2
  exit 1
fi

echo "Running converter..."
$PYTHON_BIN "$PY_SCRIPT"

if [[ -f "$OUTPUT_MMD" ]]; then
  echo "Successfully generated $OUTPUT_MMD";
  echo "Preview (first 20 lines):"
  head -n 20 "$OUTPUT_MMD"
else
  echo "Failed to generate $OUTPUT_MMD" >&2
  exit 1
fi
