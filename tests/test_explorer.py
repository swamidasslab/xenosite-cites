"""Tests for explorer payload builder."""

from __future__ import annotations

from xenosite.cites.explorer import build_explorer_payload, write_explorer_payload


def test_build_explorer_payload_slims_fields(tmp_path) -> None:
    papers = [
        {
            "openalex_id": "https://openalex.org/W1",
            "is_seed": True,
            "seed_id": "seed-a",
            "title": "Seed",
            "year": 2013,
            "doi": "10.1/a",
            "venue": "J",
            "seed_tags": ["xenosite"],
            "cited_by_count": 10,
            "abstract": "long seed abstract",
            "referenced_works": ["x"],
        },
        {
            "openalex_id": "https://openalex.org/W2",
            "is_seed": False,
            "title": "Citer",
            "year": 2020,
            "doi": "10.1/b",
            "venue": "V",
            "cites_seed_ids": ["seed-a"],
            "cited_by_count": 3,
            "abstract": "should not appear in slim paper",
            "referenced_works": ["y"],
        },
    ]
    classifications = [
        {
            "openalex_id": "https://openalex.org/W2",
            "label": "experimental",
            "topic_id": 1,
            "topic_weight": 0.8,
            "predict_then_test_confidence": "high",
            "predict_then_test_score": 5,
        }
    ]
    ptt = [
        {
            "openalex_id": "https://openalex.org/W2",
            "doi": "10.1/b",
            "title": "Citer",
            "year": 2020,
            "venue": "V",
            "cites_seed_ids": ["seed-a"],
            "confidence": "high",
            "score": 5,
            "reasons": ["xenosite", "microsome"],
            "abstract": " ".join(["word"] * 200),
        }
    ]
    payload = build_explorer_payload(
        papers=papers,
        summary={"n_citing_papers": 1},
        analysis_summary={"n_citing": 1},
        classifications=classifications,
        predict_then_test=ptt,
        competitors={"families": []},
    )
    citing = next(p for p in payload["papers"] if not p["is_seed"])
    assert "abstract" not in citing
    assert "referenced_works" not in citing
    assert citing["class_label"] == "experimental"
    assert citing["topic_id"] == 1
    assert payload["predict_then_test"][0]["abstract"] is not None
    assert len(payload["predict_then_test"][0]["abstract"]) <= 401

    out = tmp_path / "explorer.json"
    write_explorer_payload(payload, out)
    assert out.is_file()
