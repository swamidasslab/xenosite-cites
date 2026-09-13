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

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
