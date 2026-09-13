# Lab log

## 2026-09-13

- Expanded seeds to 17 XenoSite-family method papers (XenoSite, CASA, Rainbow, Forest, XenoNet, reactivity/epoxidation/quinone/UGT/N-dealkylation, etc.). CASA mapped to Dang 2017 structural alerts (`10.1021/acs.chemrestox.6b00336`).
- Added OpenAlex client + Snakemake workflow (`workflow/Snakefile`) to resolve seeds, fetch citing works (abstract + bib + referenced_works), and build `papers.jsonl` / `edges.jsonl`.
- Bulk payloads under `artifacts/` (gitignored); `data/summary.json` committed after graph builds.

## 2026-09-13 (earlier)

- Initialized from `swamidasslab/template-py-project` as private `swamidasslab/xenosite-cites`.
- Leaf package `xenosite.cites` with curated `seeds.yaml`.
