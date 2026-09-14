#!/usr/bin/env bash
# Build the GitHub Pages site tree under docs/ (figures + static marimo explorer).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

uv run xenosite-cites analyze \
  --papers artifacts/graph/papers.jsonl \
  --summary artifacts/graph/summary.json \
  --out-dir artifacts/analysis \
  --figures-dir docs/figures \
  --data-dir data/analysis \
  --explorer-public apps/public/explorer.json \
  --competitors data/competitors.json

rm -rf docs/explore
mkdir -p docs/explore
uv run marimo export html-wasm apps/explore.py \
  -o docs/explore \
  --mode run \
  --no-show-code \
  --force

touch docs/.nojekyll

BUILD_ISO="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
BUILD_DISPLAY="$(date -u +'%Y-%m-%d %H:%M UTC')"
python3 - <<PY
from pathlib import Path
path = Path("docs/index.html")
text = path.read_text(encoding="utf-8")
text = text.replace("__BUILD_ISO__", "${BUILD_ISO}")
text = text.replace("__BUILD_DISPLAY__", "${BUILD_DISPLAY}")
path.write_text(text, encoding="utf-8")
Path("docs/build-info.json").write_text(
    '{"built_at_utc": "${BUILD_ISO}"}\n', encoding="utf-8"
)
print("stamped", "${BUILD_ISO}")
print("explorer -> docs/explore/")
PY
