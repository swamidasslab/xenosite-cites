# Usage

```bash
uv sync --group workflow --group dev
```

## Seeds

```python
from xenosite.cites import load_seeds

seeds = load_seeds()
assert seeds[0].normalized_doi().startswith("10.")
```

Edit `src/xenosite/cites/seeds.yaml` to add or retire seed papers.

## Citation graph (Snakemake)

```bash
uv run snakemake -c1 -s workflow/Snakefile
```

CLI (same steps the workflow runs):

```bash
uv run python -m xenosite.cites.cli resolve-seed --seed-id zaretzki-2013-xenosite --output artifacts/openalex/seeds/zaretzki-2013-xenosite.json
uv run python -m xenosite.cites.cli fetch-citing --seed-json artifacts/openalex/seeds/zaretzki-2013-xenosite.json --output artifacts/openalex/citing/zaretzki-2013-xenosite.jsonl
```

Each citing record keeps title, year, DOI, authors, venue, abstract, and `referenced_works` (OpenAlex IDs). The graph merge records which seed IDs each paper cites.

## Figures / GitHub Pages

PNGs under `docs/figures/` are **gitignored**. They are rendered during the
Pages deploy from committed `artifacts/graph/` data and shown on
`docs/index.html`.

```bash
# Local preview of charts
uv run xenosite-cites analyze
open docs/index.html

# Interactive explorer (browser WASM via static export)
bash scripts/build_pages.sh
python -m http.server -d docs
# http://127.0.0.1:8000/explore/
```
