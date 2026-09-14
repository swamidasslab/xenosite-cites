# Lab log

## 2026-09-13

- SOM software comparison on Pages/explorer: `data/competitors.json` now tags categories (som/suite/metabolite/related) and includes XenoSite SOM-seed subset (370 unique) vs full suite (777). Gallery figure `competitor_families.png`; explorer section moved to top with category filter.

## 2026-09-13

- Static marimo explorer on Pages: `apps/explore.py` + slim `explorer.json` (filters, charts, PTT, competitor family unions). `scripts/build_pages.sh` runs analyze then `marimo export html-wasm` into `docs/explore/` (gitignored; built on deploy).

## 2026-09-13

- PNGs moved out of git: `docs/figures/*.png` gitignored; Pages workflow regenerates charts on every deploy and deploys `docs/index.html` gallery with a build timestamp. Citation/analysis JSON still committed.

## 2026-09-13

- Incremental update (`update-citations`): preserve citing jsonl order, append new IDs only, skip file write if bytes unchanged; skip `cited_by_count` churn unless `--update-volatile` / `--full`.
- Track `artifacts/openalex` (+ graph) in git; weekly Action `weekly-citation-update.yml` runs `scripts/update_and_analyze.sh` and commits.

## 2026-09-13

- Class rule changed: any wet-lab cue → `experimental`; `computational` is computation-only (dropped `mixed`). Recount: experimental 350, computational 245, review 46, unknown 136.
- Predict-then-test: infer XenoSite use from seed citation + metabolism + computational/experimental pairing so lab terbinafine papers (2018/2019) rank high without naming the tool in abstracts.
- Recent citation pace ~1.5–2 citing papers/week (2025–2026). Top recent seeds: epoxidation 2015, XenoSite 2013, Metabolic Rainbow 2020; Rainbow share up vs 2021–2023, XenoSite 2013 share down.
- Epoxidation leads partly from early ACS Cent. Sci. DL reactive-metabolite visibility and co-citation with the reactivity suite; a few synthetic-chemistry “epoxidation” papers also cite it (likely topic bleed).

## 2026-09-13

- Ran `uv run snakemake -c1 -s workflow/Snakefile`: 17 seeds → 777 citing papers, 1268 edges; 566/794 papers have abstracts; 201 multi-seed citers. Summary in `data/summary.json`; full payloads under `artifacts/`.
- Analysis: heuristic classes on 777 citers (computational 245, mixed 230, experimental 120, review 46, unknown 136); 8 NMF topics; figures in docs/figures/.
- Predict-then-test detector: title/abstract heuristics for XenoSite-family tool use followed by experimental testing; 17 high / 1 medium / 50 low on current corpus (`data/analysis/predict_then_test.jsonl`).

## 2026-09-13

- Expanded seeds to 17 XenoSite-family method papers (XenoSite, CASA, Rainbow, Forest, XenoNet, reactivity/epoxidation/quinone/UGT/N-dealkylation, etc.). CASA mapped to Dang 2017 structural alerts (`10.1021/acs.chemrestox.6b00336`).
- Added OpenAlex client + Snakemake workflow (`workflow/Snakefile`) to resolve seeds, fetch citing works (abstract + bib + referenced_works), and build `papers.jsonl` / `edges.jsonl`.
- Bulk payloads under `artifacts/` (gitignored); `data/summary.json` committed after graph builds.

## 2026-09-13 (earlier)

- Initialized from `swamidasslab/template-py-project` as private `swamidasslab/xenosite-cites`.
- Leaf package `xenosite.cites` with curated `seeds.yaml`.
