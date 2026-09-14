# xenosite-cites

Systematic study of **citations to XenoSite-family papers**: curated seeds, OpenAlex citation retrieval, and a reproducible graph build.

Import package: `xenosite.cites` (PEP 420 namespace under `xenosite`).

## Goals

1. Curate the seed set (`src/xenosite/cites/seeds.yaml`).
2. Pull citing works from OpenAlex into `artifacts/` (bib metadata, abstracts, reference lists).
3. Build citation edges and summaries for graph / bibliometric analysis.

## Citation workflow

```bash
uv sync --group workflow --group dev
uv run snakemake -c1 -s workflow/Snakefile
```

Analysis (class labels, NMF topics, figures) is included in that DAG. Analysis
JSON lands in `data/analysis/`. **PNG figures and the marimo WASM explorer are
not committed**; the [Pages workflow](.github/workflows/pages.yml) regenerates
them into `docs/` and deploys [docs/index.html](docs/index.html) plus
[docs/explore/](docs/explore/) (interactive filters over the same payload).

```bash
# Local Pages tree (figures + static explorer)
bash scripts/build_pages.sh
python -m http.server -d docs
# then open http://127.0.0.1:8000/ and /explore/
```

Local edit of the explorer notebook:

```bash
uv run marimo edit apps/explore.py
```

### Incremental updates

OpenAlex citing payloads under `artifacts/openalex/` are **tracked in git**. Refresh without a full refetch:

```bash
# Uses update_manifest.json (minus 14-day overlap); appends new rows; rewrites
# existing rows only when bibliographic fields improve. Citation counts are
# left alone unless --update-volatile or --full.
uv run xenosite-cites update-citations

# Then rebuild graph + analysis (or use the helper):
bash scripts/update_and_analyze.sh
```

Local `docs/figures/*.png` stay gitignored. A weekly Action updates citation
data; a separate Pages deploy rebuilds charts for the site.

Enable **Settings → Pages → Source: GitHub Actions**. The site can be public;
pages ship with `noindex, noarchive` and a disallow-all `robots.txt`.

Outputs:

| Path | Role |
|------|------|
| `artifacts/openalex/seeds/{id}.json` | Resolved seed works |
| `artifacts/openalex/citing/{id}.jsonl` | Papers citing each seed (abstract + bib + `referenced_works`) |
| `artifacts/openalex/update_manifest.json` | Last incremental update metadata |
| `artifacts/graph/papers.jsonl` | Deduplicated paper nodes |
| `artifacts/graph/edges.jsonl` | Citing → seed edges |
| `artifacts/graph/summary.json` | Counts |
| `data/summary.json` | Same summary, tracked in git |
| `docs/index.html` | Gallery page (PNGs filled in at Pages deploy) |
| `docs/explore/` | Static marimo WASM explorer (built on Pages deploy) |
| `apps/explore.py` | Explorer notebook source |
| `apps/public/explorer.json` | Slim analysis payload for the explorer |

## Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check
uv run ruff format --check
uv run mypy src
```

```python
from xenosite.cites import load_seeds

for paper in load_seeds():
    print(paper.year, paper.doi, paper.title)
```

Version comes from git tags (`vX.Y.Z`). See [docs/release.md](docs/release.md).
