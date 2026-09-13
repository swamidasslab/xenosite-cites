"""Tests for graph merge logic (no network)."""

from __future__ import annotations

import json
from pathlib import Path

from xenosite.cites.cli import cmd_build_graph


def test_build_graph_merges_multi_seed_citers(tmp_path: Path) -> None:
    seed_a = {
        "seed": {
            "seed_id": "a",
            "openalex_id": "https://openalex.org/WA",
            "doi": "10.1/a",
            "title": "Seed A",
            "year": 2010,
            "authors": ["A"],
            "venue": "J",
            "abstract": "Seed A abstract",
            "referenced_works": [],
            "seed_tags": ["xenosite"],
            "seed_notes": "",
        }
    }
    seed_b = {
        "seed": {
            "seed_id": "b",
            "openalex_id": "https://openalex.org/WB",
            "doi": "10.1/b",
            "title": "Seed B",
            "year": 2011,
            "authors": ["B"],
            "venue": "J",
            "abstract": "Seed B abstract",
            "referenced_works": [],
            "seed_tags": ["xenonet"],
            "seed_notes": "",
        }
    }
    seeds_dir = tmp_path / "seeds"
    citing_dir = tmp_path / "citing"
    out_dir = tmp_path / "graph"
    seeds_dir.mkdir()
    citing_dir.mkdir()
    (seeds_dir / "a.json").write_text(json.dumps(seed_a), encoding="utf-8")
    (seeds_dir / "b.json").write_text(json.dumps(seed_b), encoding="utf-8")

    citing = {
        "openalex_id": "https://openalex.org/WC",
        "doi": "10.1/c",
        "title": "Citer",
        "year": 2020,
        "authors": ["C"],
        "venue": "J",
        "abstract": "Cites both seeds",
        "referenced_works": ["https://openalex.org/WA", "https://openalex.org/WB"],
        "cites_seed_id": "a",
        "cites_seed_openalex_id": "https://openalex.org/WA",
        "cites_seed_doi": "10.1/a",
    }
    (citing_dir / "a.jsonl").write_text(json.dumps(citing) + "\n", encoding="utf-8")
    citing_b = dict(citing)
    citing_b["cites_seed_id"] = "b"
    citing_b["cites_seed_openalex_id"] = "https://openalex.org/WB"
    citing_b["cites_seed_doi"] = "10.1/b"
    (citing_dir / "b.jsonl").write_text(json.dumps(citing_b) + "\n", encoding="utf-8")

    class Args:
        seed_json = [str(seeds_dir / "a.json"), str(seeds_dir / "b.json")]
        citing_jsonl = [str(citing_dir / "a.jsonl"), str(citing_dir / "b.jsonl")]
        out_dir = str(out_dir)
        summary_copy = str(tmp_path / "summary.json")

    cmd_build_graph(Args())
    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["n_seeds"] == 2
    assert summary["n_edges"] == 2
    assert summary["n_citing_papers"] == 1
    papers = [
        json.loads(line)
        for line in (out_dir / "papers.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    citer = next(p for p in papers if p["openalex_id"] == "https://openalex.org/WC")
    assert sorted(citer["cites_seed_ids"]) == ["a", "b"]
    assert sorted(citer["references_seed_ids"]) == ["a", "b"]
    assert citer["abstract"] == "Cites both seeds"
