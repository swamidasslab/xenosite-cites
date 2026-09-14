"""Build a browser-friendly explorer payload for the static marimo app."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _short_abstract(text: str | None, *, limit: int = 400) -> str | None:
    if not text:
        return None
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def build_explorer_payload(
    *,
    papers: list[dict[str, Any]],
    summary: dict[str, Any],
    analysis_summary: dict[str, Any],
    classifications: list[dict[str, Any]],
    predict_then_test: list[dict[str, Any]],
    competitors: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble a slim JSON payload for interactive exploration."""
    by_id = {str(row.get("openalex_id") or ""): row for row in classifications}
    slim_papers: list[dict[str, Any]] = []
    for paper in papers:
        oid = str(paper.get("openalex_id") or "")
        if paper.get("is_seed"):
            slim_papers.append(
                {
                    "openalex_id": oid,
                    "seed_id": paper.get("seed_id"),
                    "title": paper.get("title"),
                    "year": paper.get("year"),
                    "doi": paper.get("doi"),
                    "venue": paper.get("venue"),
                    "is_seed": True,
                    "seed_tags": list(paper.get("seed_tags") or []),
                    "cited_by_count": paper.get("cited_by_count"),
                }
            )
            continue
        row = by_id.get(oid) or {}
        slim_papers.append(
            {
                "openalex_id": oid,
                "title": paper.get("title"),
                "year": paper.get("year"),
                "doi": paper.get("doi"),
                "venue": paper.get("venue"),
                "is_seed": False,
                "cites_seed_ids": list(paper.get("cites_seed_ids") or []),
                "cited_by_count": paper.get("cited_by_count"),
                "class_label": row.get("label"),
                "topic_id": row.get("topic_id"),
                "topic_weight": row.get("topic_weight"),
                "predict_then_test_confidence": row.get("predict_then_test_confidence"),
                "predict_then_test_score": row.get("predict_then_test_score"),
            }
        )

    ptt_rows: list[dict[str, Any]] = []
    for row in predict_then_test:
        ptt_rows.append(
            {
                "openalex_id": row.get("openalex_id"),
                "doi": row.get("doi"),
                "title": row.get("title"),
                "year": row.get("year"),
                "venue": row.get("venue"),
                "cites_seed_ids": list(row.get("cites_seed_ids") or []),
                "confidence": row.get("confidence"),
                "score": row.get("score"),
                "reasons": row.get("reasons"),
                "abstract": _short_abstract(row.get("abstract")),
            }
        )

    return {
        "summary": summary,
        "analysis": analysis_summary,
        "papers": slim_papers,
        "predict_then_test": ptt_rows,
        "competitors": competitors or {},
    }


def write_explorer_payload(payload: dict[str, Any], *paths: Path) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def load_competitors(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}
