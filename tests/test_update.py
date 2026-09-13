from xenosite.cites.update import merge_citing_records, merge_record, write_text_if_changed


def test_merge_preserves_order_and_appends_new() -> None:
    existing = [
        {"openalex_id": "W1", "title": "First", "year": 2020, "abstract": "a"},
        {"openalex_id": "W2", "title": "Second", "year": 2021, "abstract": "b"},
    ]
    incoming = [
        {"openalex_id": "W3", "title": "New B", "year": 2022},
        {"openalex_id": "W4", "title": "New A", "year": 2022},
        {"openalex_id": "W1", "title": "First", "year": 2020, "abstract": "a", "doi": "10.1/x"},
    ]
    merged, n_added, n_updated = merge_citing_records(existing, incoming)
    assert [r["openalex_id"] for r in merged] == ["W1", "W2", "W4", "W3"]
    assert n_added == 2
    assert n_updated == 1
    assert merged[0]["doi"] == "10.1/x"
    assert merged[0]["abstract"] == "a"


def test_merge_skips_volatile_by_default() -> None:
    prior = {"openalex_id": "W1", "title": "T", "cited_by_count": 1}
    incoming = {"openalex_id": "W1", "title": "T", "cited_by_count": 99, "abstract": "hi"}
    merged = merge_record(prior, incoming)
    assert merged["cited_by_count"] == 1
    assert merged["abstract"] == "hi"
    merged_v = merge_record(prior, incoming, update_volatile=True)
    assert merged_v["cited_by_count"] == 99


def test_merge_no_update_when_identical() -> None:
    existing = [{"openalex_id": "W1", "title": "T", "year": 2020}]
    incoming = [{"openalex_id": "W1", "title": "T", "year": 2020, "cited_by_count": 5}]
    merged, n_added, n_updated = merge_citing_records(existing, incoming)
    assert n_added == 0
    assert n_updated == 0
    assert merged == existing


def test_write_text_if_changed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "f.txt"
    assert write_text_if_changed(path, "a\n") is True
    assert write_text_if_changed(path, "a\n") is False
    assert write_text_if_changed(path, "b\n") is True
