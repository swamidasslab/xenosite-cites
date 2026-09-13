# xenosite-cites

Systematic study of **citations to XenoSite papers**: seed corpus, citation retrieval, and analyses of who cites the work and how.

Import package: `xenosite.cites` (PEP 420 namespace under `xenosite`).

## Goals

1. Curate the seed set of XenoSite / related papers (`seeds.yaml`).
2. Pull citing works from bibliographic APIs (e.g. OpenAlex) into `artifacts/`.
3. Summarize citation counts, venues, topics, and self- vs external citation patterns.

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

## Layout

| Path | Role |
|------|------|
| `src/xenosite/cites/seeds.yaml` | Curated seed DOIs (tracked) |
| `artifacts/` | Downloaded citation payloads (gitignored) |
| `docs/usage.md` | Usage notes |
