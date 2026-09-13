from xenosite.cites.predict_then_test import score_predict_then_test


def test_high_confidence_brexpiprazole_style() -> None:
    paper = {
        "title": ("In silico, in vitro and in vivo metabolite identification of brexpiprazole"),
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
