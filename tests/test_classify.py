from xenosite.cites.classify import classify_paper


def test_classify_review_from_openalex_type() -> None:
    result = classify_paper({"title": "Something", "abstract": "", "type": "review"})
    assert result["label"] == "review"


def test_classify_computational_only() -> None:
    result = classify_paper(
        {
            "title": "Deep learning prediction of sites of metabolism",
            "abstract": "We train a neural network on in silico descriptors.",
            "type": "article",
        }
    )
    assert result["label"] == "computational"
    assert result["computation_only"]
    assert not result["has_wet_lab"]


def test_classify_experimental_keywords() -> None:
    result = classify_paper(
        {
            "title": "Microsomal metabolism of compound X",
            "abstract": "Human liver microsomes were incubated and metabolites identified by LC-MS.",
            "type": "article",
        }
    )
    assert result["label"] == "experimental"
    assert result["has_wet_lab"]


def test_wet_lab_beats_computation() -> None:
    result = classify_paper(
        {
            "title": "Computational and experimental study",
            "abstract": "Docking predictions were validated in vitro using microsomes.",
            "type": "article",
        }
    )
    assert result["label"] == "experimental"
    assert result["has_wet_lab"]
    assert result["computational_hits"] > 0
    assert not result["computation_only"]
