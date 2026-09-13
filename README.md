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

Analysis (class labels, NMF topics, figures) is included in that DAG. Figures land in `docs/figures/`; a short write-up is in `data/analysis/analysis_report.md`.

Outputs:

| Path | Role |
|------|------|
| `artifacts/openalex/seeds/{id}.json` | Resolved seed works |
| `artifacts/openalex/citing/{id}.jsonl` | Papers citing each seed (abstract + bib + `referenced_works`) |
| `artifacts/graph/papers.jsonl` | Deduplicated paper nodes |
| `artifacts/graph/edges.jsonl` | Citing → seed edges |
| `artifacts/graph/summary.json` | Counts |
| `data/summary.json` | Same summary, tracked in git |

Bulk OpenAlex payloads stay under `artifacts/` (gitignored). Re-run Snakemake to refresh.

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
