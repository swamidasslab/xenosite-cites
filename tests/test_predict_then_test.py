from xenosite.cites.predict_then_test import score_predict_then_test


def test_high_confidence_brexpiprazole_style() -> None:
    paper = {
        "title": (
            "In silico, in vitro and in vivo metabolite identification of brexpiprazole"
        ),
        "abstract": (
            "Firstly, the site of metabolism for brexpiprazole was predicted by a "
            "Xenosite web predictor model. Secondly, in vitro metabolite profiling was "
            "performed by incubating the drug individually with rat liver microsomes "
            "and metabolites were identified by LC-MS."
        ),
    }
    result = score_predict_then_test(paper)
    assert result["confidence"] == "high"
    assert result["tool_used_to_predict"]
    assert result["experimental_hits"] >= 2
    assert result["predict_then_test_narrative"]


def test_excludes_benchmark_against_xenosite() -> None:
    paper = {
        "title": "Machine Learning Enables Accurate Prediction of Quinone Formation",
        "abstract": (
            "Developed models were compared to the existing Xenosite web server using "
            "the untouched test set of 102 molecules."
        ),
    }
    result = score_predict_then_test(paper)
    assert result["benchmark_against_tool"]
    assert result["confidence"] == "none"


def test_medium_when_named_with_experiment_but_weak_use() -> None:
    paper = {
        "title": "Metabolism study",
        "abstract": (
            "XenoSite was considered among available servers. Human liver microsomes "
            "were incubated and metabolites characterized by LC-MS."
        ),
    }
    result = score_predict_then_test(paper)
    assert result["tool_named"]
    assert result["confidence"] in {"medium", "high"}


def test_silico_vitro_without_tool_name_is_low() -> None:
    paper = {
        "title": "In silico and in vitro metabolism of drug X",
        "abstract": (
            "Sites of metabolism were predicted in silico. Subsequently in vitro "
            "microsomal incubations and LC-MS identified metabolites."
        ),
    }
    result = score_predict_then_test(paper)
    assert not result["tool_named"]
    assert result["confidence"] == "low"


def test_terbinafine_inferred_from_seed_citation() -> None:
    """Lab terbinafine papers cite XenoSite seeds but often omit the product name."""
    paper = {
        "title": (
            "CYP2C19 and 3A4 Dominate Metabolic Clearance and Bioactivation of "
            "Terbinafine Based on Computational and Experimental Approaches"
        ),
        "abstract": (
            "We characterized pathways using in vitro studies with human liver "
            "microsomes and modeling approaches. Herein, we employed experimental "
            "and computational tools to assess terbinafine metabolism."
        ),
        "cites_seed_ids": ["zaretzki-2013-xenosite", "dang-2018-n-dealkylation"],
    }
    result = score_predict_then_test(paper)
    assert result["confidence"] == "high"
    assert result["tool_inferred_from_seed_citation"]
    assert "zaretzki-2013-xenosite" in result["cites_seed_ids"]


def test_terbinafine_title_only_with_seed_citation() -> None:
    paper = {
        "title": (
            "Lamisil (terbinafine) toxicity: Determining pathways to bioactivation "
            "through computational and experimental approaches"
        ),
        "abstract": "",
        "cites_seed_ids": ["dang-2018-n-dealkylation"],
    }
    result = score_predict_then_test(paper)
    assert result["confidence"] in {"high", "medium"}
    assert result["computational_and_experimental"]
