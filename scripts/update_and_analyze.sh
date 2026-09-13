#!/usr/bin/env bash
# Incremental OpenAlex citation update, then rebuild graph + analysis.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MAILTO="${OPENALEX_MAILTO:-swamidass@gmail.com}"
UPDATE_ARGS=()
if [[ "${FULL_REFRESH:-0}" == "1" ]]; then
  UPDATE_ARGS+=(--full)
fi
if [[ -n "${SINCE:-}" ]]; then
  UPDATE_ARGS+=(--since "$SINCE")
fi

echo "[update_and_analyze] update-citations ${UPDATE_ARGS[*]:-}"
uv run xenosite-cites --mailto "$MAILTO" update-citations --artifacts-dir artifacts "${UPDATE_ARGS[@]}"

SEED_JSON=(artifacts/openalex/seeds/*.json)
CITING_JSONL=(artifacts/openalex/citing/*.jsonl)

echo "[update_and_analyze] build-graph"
uv run xenosite-cites build-graph \
  --seed-json "${SEED_JSON[@]}" \
  --citing-jsonl "${CITING_JSONL[@]}" \
  --out-dir artifacts/graph \
  --summary-copy data/summary.json

echo "[update_and_analyze] analyze"
uv run xenosite-cites analyze \
  --papers artifacts/graph/papers.jsonl \
  --summary artifacts/graph/summary.json \
  --out-dir artifacts/analysis \
  --figures-dir docs/figures \
  --data-dir data/analysis

echo "[update_and_analyze] done"
