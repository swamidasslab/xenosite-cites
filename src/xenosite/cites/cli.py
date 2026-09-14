"""CLI entry points used by the Snakemake citation workflow."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from xenosite.cites.openalex import OpenAlexClient, work_record
from xenosite.cites.seeds import load_seeds


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def cmd_resolve_seed(args: argparse.Namespace) -> None:
    seeds = {s.id: s for s in load_seeds()}
    seed = seeds[args.seed_id]
    with OpenAlexClient(mailto=args.mailto) as client:
        raw = client.work_by_doi(seed.normalized_doi())
    record = work_record(raw)
    record["seed_id"] = seed.id
    record["seed_tags"] = list(seed.tags)
    record["seed_notes"] = seed.notes
    _write_json(Path(args.output), {"seed": record, "raw_openalex_id": raw.get("id")})


def cmd_fetch_citing(args: argparse.Namespace) -> None:
    seed_payload = json.loads(Path(args.seed_json).read_text(encoding="utf-8"))
    seed = seed_payload["seed"]
    openalex_id = seed["openalex_id"]
    rows: list[dict[str, Any]] = []
    with OpenAlexClient(mailto=args.mailto) as client:
        for work in client.iter_citing_works(openalex_id):
            record = work_record(work)
            record["cites_seed_id"] = seed["seed_id"]
            record["cites_seed_openalex_id"] = openalex_id
            record["cites_seed_doi"] = seed.get("doi")
            rows.append(record)
    _write_jsonl(Path(args.output), rows)


def cmd_build_graph(args: argparse.Namespace) -> None:
    seed_paths = [Path(p) for p in args.seed_json]
    citing_paths = [Path(p) for p in args.citing_jsonl]

    papers: dict[str, dict[str, Any]] = {}
    seed_oa_ids: dict[str, str] = {}
    seed_by_oa: dict[str, str] = {}
    edges: list[dict[str, Any]] = []

    for path in seed_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        seed = payload["seed"]
        oa = seed["openalex_id"]
        seed_id = seed["seed_id"]
        seed_oa_ids[seed_id] = oa
        seed_by_oa[oa] = seed_id
        papers[oa] = {
            **seed,
            "is_seed": True,
            "cites_seed_ids": [],
        }

    for path in citing_paths:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                citing = json.loads(line)
                oa = citing["openalex_id"]
                seed_id = citing["cites_seed_id"]
                cited_oa = citing["cites_seed_openalex_id"]
                edges.append(
                    {
                        "citing_openalex_id": oa,
                        "cited_openalex_id": cited_oa,
                        "cited_seed_id": seed_id,
                        "citing_doi": citing.get("doi"),
                        "cited_doi": citing.get("cites_seed_doi"),
                    }
                )
                existing = papers.get(oa)
                if existing is None:
                    papers[oa] = {
                        **{k: v for k, v in citing.items() if not k.startswith("cites_seed")},
                        "is_seed": False,
                        "cites_seed_ids": [seed_id],
                    }
                else:
                    cites = list(existing.get("cites_seed_ids") or [])
                    if seed_id not in cites:
                        cites.append(seed_id)
                    existing["cites_seed_ids"] = sorted(cites)
                    # Prefer non-empty abstract / richer fields if a later fetch has them.
                    if not existing.get("abstract") and citing.get("abstract"):
                        existing["abstract"] = citing["abstract"]
                    if not existing.get("doi") and citing.get("doi"):
                        existing["doi"] = citing["doi"]

    # Annotate each paper with which seed OpenAlex IDs appear in referenced_works.
    for paper in papers.values():
        referenced = set(paper.get("referenced_works") or [])
        paper["references_seed_ids"] = sorted(
            seed_by_oa[oa] for oa in referenced if oa in seed_by_oa
        )

    paper_rows = sorted(
        papers.values(),
        key=lambda p: (not p.get("is_seed"), p.get("year") or 0, p.get("title") or ""),
    )
    out_dir = Path(args.out_dir)
    _write_jsonl(out_dir / "papers.jsonl", paper_rows)
    _write_jsonl(out_dir / "edges.jsonl", edges)

    seed_cite_counts = Counter(e["cited_seed_id"] for e in edges)
    citing_counts = Counter(e["citing_openalex_id"] for e in edges)
    summary = {
        "n_seeds": len(seed_paths),
        "n_papers": len(paper_rows),
        "n_citing_papers": sum(1 for p in paper_rows if not p.get("is_seed")),
        "n_edges": len(edges),
        "n_citing_papers_multi_seed": sum(1 for c in citing_counts.values() if c > 1),
        "citations_per_seed": dict(sorted(seed_cite_counts.items())),
        "papers_with_abstract": sum(1 for p in paper_rows if p.get("abstract")),
        "papers_with_doi": sum(1 for p in paper_rows if p.get("doi")),
    }
    _write_json(out_dir / "summary.json", summary)
    # Small committed-friendly copy when requested.
    if args.summary_copy:
        _write_json(Path(args.summary_copy), summary)


def cmd_analyze(args: argparse.Namespace) -> None:
    from xenosite.cites import plots
    from xenosite.cites.classify import classify_paper
    from xenosite.cites.explorer import (
        build_explorer_payload,
        load_competitors,
        write_explorer_payload,
    )
    from xenosite.cites.predict_then_test import score_predict_then_test
    from xenosite.cites.topics import fit_topics

    papers_path = Path(args.papers)
    summary_path = Path(args.summary)
    out_dir = Path(args.out_dir)
    fig_dir = Path(args.figures_dir)
    data_dir = Path(args.data_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    papers = [
        json.loads(line)
        for line in papers_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    citing = [p for p in papers if not p.get("is_seed")]

    classifications: list[dict[str, Any]] = []
    label_by_id: dict[str, str] = {}
    predict_then_test_rows: list[dict[str, Any]] = []
    for paper in citing:
        result = classify_paper(paper)
        ptt = score_predict_then_test(paper)
        oid = str(paper.get("openalex_id") or "")
        label_by_id[oid] = result["label"]
        classifications.append(
            {
                "openalex_id": oid,
                "doi": paper.get("doi"),
                "title": paper.get("title"),
                "year": paper.get("year"),
                "venue": paper.get("venue"),
                **result,
                "predict_then_test_confidence": ptt["confidence"],
                "predict_then_test_score": ptt["score"],
            }
        )
        if ptt["confidence"] != "none":
            predict_then_test_rows.append(
                {
                    "openalex_id": oid,
                    "doi": paper.get("doi"),
                    "title": paper.get("title"),
                    "year": paper.get("year"),
                    "venue": paper.get("venue"),
                    "abstract": paper.get("abstract"),
                    "cites_seed_ids": paper.get("cites_seed_ids") or [],
                    **ptt,
                }
            )

    topic_fit = fit_topics(citing, n_topics=args.n_topics)
    topic_by_id = {a["openalex_id"]: a for a in topic_fit.get("assignments") or []}
    for row in classifications:
        assignment = topic_by_id.get(row["openalex_id"])
        if assignment:
            row["topic_id"] = assignment["topic_id"]
            row["topic_weight"] = assignment["topic_weight"]
        else:
            row["topic_id"] = None
            row["topic_weight"] = None

    predict_then_test_rows.sort(
        key=lambda r: (
            {"high": 0, "medium": 1, "low": 2}.get(r["confidence"], 9),
            -int(r["score"]),
            r.get("year") or 0,
        )
    )
    ptt_counts = Counter(r["confidence"] for r in predict_then_test_rows)
    class_counts = Counter(r["label"] for r in classifications)
    analysis_summary = {
        "n_citing": len(citing),
        "class_counts": dict(sorted(class_counts.items())),
        "predict_then_test_counts": dict(sorted(ptt_counts.items())),
        "n_predict_then_test_high_medium": sum(
            1 for r in predict_then_test_rows if r["confidence"] in {"high", "medium"}
        ),
        "topics": topic_fit.get("topics") or [],
        "n_topic_docs": topic_fit.get("n_docs"),
        "reconstruction_error": topic_fit.get("reconstruction_error"),
        "pre_2012_citing": sum(
            1 for p in citing if isinstance(p.get("year"), int) and p["year"] < 2012
        ),
    }

    _write_jsonl(out_dir / "classifications.jsonl", classifications)
    _write_jsonl(out_dir / "predict_then_test.jsonl", predict_then_test_rows)
    _write_json(out_dir / "topics.json", topic_fit)
    _write_json(out_dir / "analysis_summary.json", analysis_summary)
    _write_json(data_dir / "analysis_summary.json", analysis_summary)
    _write_json(data_dir / "topics.json", {"topics": topic_fit.get("topics") or []})
    _write_jsonl(data_dir / "predict_then_test.jsonl", predict_then_test_rows)

    labels = [r["label"] for r in classifications]
    competitors = load_competitors(Path(args.competitors))
    fig_writer = plots.FigureWriter(fig_dir)
    plots.plot_citations_by_year(papers, fig_writer)
    plots.plot_top_venues(papers, fig_writer)
    plots.plot_citations_per_seed(summary, fig_writer)
    plots.plot_class_counts(labels, fig_writer)
    plots.plot_class_by_year(papers, label_by_id, fig_writer)
    plots.plot_topic_sizes(topic_fit.get("topics") or [], fig_writer)
    plots.plot_predict_then_test_counts(
        [r["confidence"] for r in predict_then_test_rows],
        fig_writer,
    )
    plots.plot_competitor_families(competitors, fig_writer)
    fig_writer.flush()
    print(f"[analyze] figures written={fig_writer.n_written}", flush=True)

    art_fig = out_dir / "figures"
    art_fig.mkdir(parents=True, exist_ok=True)
    for name in (
        "citations_by_year.png",
        "top_venues.png",
        "citations_per_seed.png",
        "class_counts.png",
        "class_by_year.png",
        "topic_sizes.png",
        "predict_then_test_counts.png",
        "competitor_families.png",
    ):
        src = fig_dir / name
        if src.exists():
            dest = art_fig / name
            payload = src.read_bytes()
            if not dest.exists() or dest.read_bytes() != payload:
                dest.write_bytes(payload)

    report_lines = [
        "# Citing-paper analysis",
        "",
        f"- Citing papers: **{len(citing)}**",
        f"- Class counts: {dict(sorted(class_counts.items()))}",
        f"- Predict-then-test (XenoSite use → experiment): "
        f"{dict(sorted(ptt_counts.items()))} "
        f"(high+medium={analysis_summary['n_predict_then_test_high_medium']})",
        f"- Topic model docs: **{topic_fit.get('n_docs')}** across "
        f"**{topic_fit.get('n_topics')}** NMF topics",
        f"- Pre-2012 citing records (likely metadata noise): "
        f"**{analysis_summary['pre_2012_citing']}**",
        "",
        "## Classes",
        "",
        "Heuristic labels from OpenAlex `type` plus title/abstract keywords "
        "(`review` / `experimental` = any wet-lab cue / `computational` = "
        "computation-only / `unknown`).",
        "",
        "## Predict-then-test",
        "",
        "Simple abstract/title detector for papers that **use a XenoSite-family tool "
        "to make predictions** and then **test experimentally** (microsomes, LC-MS, "
        "in vitro/in vivo, etc.). Benchmark-against-XenoSite papers are excluded. "
        "See `predict_then_test.jsonl`.",
        "",
        "### High confidence",
        "",
    ]
    highs = [r for r in predict_then_test_rows if r["confidence"] == "high"]
    for row in highs:
        report_lines.append(
            f"- {row.get('year')} "
            f"[{row.get('doi') or row.get('openalex_id')}] "
            f"{(row.get('title') or '')[:120]}"
        )
    if not highs:
        report_lines.append("- (none)")
    report_lines.extend(["", "## Topics", ""])
    for topic in topic_fit.get("topics") or []:
        kws = ", ".join(topic["keywords"][:8])
        report_lines.append(f"- **T{topic['topic_id']}** (n={topic['n_papers']}): {kws}")
    report_lines.extend(
        [
            "",
            "## Figures",
            "",
            "See `docs/figures/` (gitignored locally; built on GitHub Pages deploy).",
            "",
        ]
    )
    report = "\n".join(report_lines) + "\n"
    (data_dir / "analysis_report.md").write_text(report, encoding="utf-8")
    (out_dir / "analysis_report.md").write_text(report, encoding="utf-8")

    explorer = build_explorer_payload(
        papers=papers,
        summary=summary,
        analysis_summary=analysis_summary,
        classifications=classifications,
        predict_then_test=predict_then_test_rows,
        competitors=competitors,
    )
    write_explorer_payload(
        explorer,
        data_dir / "explorer.json",
        out_dir / "explorer.json",
        Path(args.explorer_public),
    )


def cmd_update_citations(args: argparse.Namespace) -> None:
    from xenosite.cites.update import update_citations

    update_citations(
        artifacts_dir=Path(args.artifacts_dir),
        mailto=args.mailto,
        since=args.since,
        full=args.full,
        overlap_days=args.overlap_days,
        update_volatile=args.update_volatile,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xenosite-cites")
    parser.add_argument("--mailto", default="swamidass@gmail.com")
    sub = parser.add_subparsers(dest="command", required=True)

    resolve = sub.add_parser("resolve-seed", help="Resolve one seed DOI via OpenAlex")
    resolve.add_argument("--seed-id", required=True)
    resolve.add_argument("--output", required=True)
    resolve.set_defaults(func=cmd_resolve_seed)

    citing = sub.add_parser("fetch-citing", help="Fetch works citing a resolved seed")
    citing.add_argument("--seed-json", required=True)
    citing.add_argument("--output", required=True)
    citing.set_defaults(func=cmd_fetch_citing)

    graph = sub.add_parser("build-graph", help="Merge seed + citing records into a graph")
    graph.add_argument("--seed-json", nargs="+", required=True)
    graph.add_argument("--citing-jsonl", nargs="+", required=True)
    graph.add_argument("--out-dir", required=True)
    graph.add_argument("--summary-copy", default=None)
    graph.set_defaults(func=cmd_build_graph)

    analyze = sub.add_parser(
        "analyze",
        help="Classify citing papers, fit topics, and write figures",
    )
    analyze.add_argument("--papers", default="artifacts/graph/papers.jsonl")
    analyze.add_argument("--summary", default="artifacts/graph/summary.json")
    analyze.add_argument("--out-dir", default="artifacts/analysis")
    analyze.add_argument("--figures-dir", default="docs/figures")
    analyze.add_argument("--data-dir", default="data/analysis")
    analyze.add_argument(
        "--explorer-public",
        default="apps/public/explorer.json",
        help="Marimo public/ copy of the explorer payload",
    )
    analyze.add_argument(
        "--competitors",
        default="data/competitors.json",
        help="Optional competitor-family unique-citer summary JSON",
    )
    analyze.add_argument("--n-topics", type=int, default=8)
    analyze.set_defaults(func=cmd_analyze)

    update = sub.add_parser(
        "update-citations",
        help="Incrementally refresh OpenAlex citing works (diff-minimizing writes)",
    )
    update.add_argument("--artifacts-dir", default="artifacts")
    update.add_argument(
        "--since",
        default=None,
        help="OpenAlex from_created_date (YYYY-MM-DD); default from last manifest",
    )
    update.add_argument(
        "--full",
        action="store_true",
        help="Ignore since/manifest and refetch all citing works",
    )
    update.add_argument("--overlap-days", type=int, default=14)
    update.add_argument(
        "--update-volatile",
        action="store_true",
        help="Also refresh cited_by_count on existing rows (more diff churn)",
    )
    update.set_defaults(func=cmd_update_citations)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
