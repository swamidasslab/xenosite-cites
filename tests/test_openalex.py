from xenosite.cites.openalex import reconstruct_abstract, work_record


def test_reconstruct_abstract_orders_tokens() -> None:
    inverted = {"world": [1], "Hello": [0], "!": [2]}
    assert reconstruct_abstract(inverted) == "Hello world !"


def test_work_record_extracts_core_fields() -> None:
    work = {
        "id": "https://openalex.org/W1",
        "doi": "https://doi.org/10.1/abc",
        "title": "Example",
        "publication_year": 2020,
        "publication_date": "2020-01-02",
        "type": "article",
        "cited_by_count": 3,
        "authorships": [{"author": {"display_name": "A Author"}}],
        "primary_location": {"source": {"display_name": "Journal"}},
        "abstract_inverted_index": {"Hi": [0]},
        "referenced_works": ["https://openalex.org/W2"],
        "cited_by_api_url": "https://api.openalex.org/works?filter=cites:W1",
        "ids": {"doi": "https://doi.org/10.1/abc"},
    }
    record = work_record(work)
    assert record["doi"] == "10.1/abc"
    assert record["authors"] == ["A Author"]
    assert record["venue"] == "Journal"
    assert record["abstract"] == "Hi"
    assert record["referenced_works"] == ["https://openalex.org/W2"]
