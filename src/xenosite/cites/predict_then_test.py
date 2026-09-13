"""Detect papers that use XenoSite-family tools then test predictions experimentally."""

from __future__ import annotations

import re
from typing import Any

# Named products / servers in the XenoSite family.
_TOOL = re.compile(
    r"\b("
    r"xenosite|xenonet|metabolic\s+forest|rainbow\s+xenosite|"
    r"rs[- ]?webpredictor|rs[- ]?predictor"
    r")\b",
    re.I,
)

# Evidence the tool was used to make predictions (not merely mentioned).
_TOOL_USE = re.compile(
    r"("
    r"(predicted|prediction|predictor|predicting).{0,60}"
    r"(xenosite|xenonet|metabolic\s+forest|rs[- ]?webpredictor)|"
    r"(xenosite|xenonet|metabolic\s+forest|rs[- ]?webpredictor).{0,80}"
    r"(predict|prediction|predictor|vulnerable\s+site|site\s+of\s+metabolism|"
    r"reactivity|bioactivation|metabol)|"
    r"(using|used|employed|investigated\s+using|performed\s+using|applied).{0,50}"
    r"(xenosite|xenonet|metabolic\s+forest|rs[- ]?webpredictor)|"
    r"xenosite\s+web\s+(predictor|server|tool)|"
    r"in\s+silico.{0,50}(xenosite|xenonet)"
    r")",
    re.I | re.S,
)

# Papers that benchmark against XenoSite rather than using it as a method.
_BENCHMARK = re.compile(
    r"("
    r"compared\s+to\s+(the\s+)?(existing\s+)?xenosite|"
    r"outperform.{0,30}xenosite|"
    r"baseline.{0,30}xenosite|"
    r"against\s+xenosite|"
    r"while\s+the\s+xenosite"
    r")",
    re.I | re.S,
)

_EXPERIMENTAL = re.compile(
    r"\b("
    r"in\s+vitro|in\s+vivo|microsom\w*|hepatocyte|s9\s+fraction|"
    r"incubat\w*|lc[- ]?ms|uhplc|hplc|metabolite\s+identif\w*|"
    r"metabolite\s+profil\w*|trap(?:ped|ping)|adduct|"
    r"confirmed|validat\w*|experimentally|reaction\s+kinetics?"
    r")\b",
    re.I,
)

# Predict-then-test narrative cues (order-ish language in abstract/title).
_NARRATIVE = re.compile(
    r"("
    r"(first(ly)?|initially|then|later|subsequently|afterwards|"
    r"followed\s+by|guided|used\s+as\s+a\s+guide|"
    r"in\s+silico\s+data\s+were\s+used).{0,140}"
    r"(in\s+vitro|in\s+vivo|microsom|incubat|lc[- ]?ms|uhplc|metabolite)|"
    r"(in\s+silico|predict\w*).{0,100}(in\s+vitro|in\s+vivo|microsom)|"
    r"(in\s+vitro|in\s+vivo).{0,60}(in\s+silico|predict\w*)"
    r")",
    re.I | re.S,
)

_TITLE_BOTH = re.compile(
    r"in\s+silico.{0,40}(in\s+vitro|in\s+vivo)|(in\s+vitro|in\s+vivo).{0,40}in\s+silico",
    re.I | re.S,
)


def _blob(paper: dict[str, Any]) -> tuple[str, str, str]:
    title = str(paper.get("title") or "")
    abstract = str(paper.get("abstract") or "")
    return title, abstract, f"{title}\n{abstract}"


def score_predict_then_test(paper: dict[str, Any]) -> dict[str, Any]:
    """Score whether a paper uses a XenoSite-family tool then tests experimentally.

    Confidence:
    - ``high``: tool used for prediction + experimental evidence + not a benchmark paper;
      narrative or dual in-silico/in-vitro title preferred but not required if use+exp strong.
    - ``medium``: tool named + experimental evidence, weaker use wording, or missing narrative.
    - ``low``: some signals but incomplete (e.g. tool use without experiment, or experiment
      without clear tool use).
    - ``none``: does not match the pattern.

    Benchmark-against-XenoSite papers are excluded from high/medium.
    """
    title, _abstract, text = _blob(paper)
    tool_named = bool(_TOOL.search(text))
    tool_used = bool(_TOOL_USE.search(text))
    benchmark = bool(_BENCHMARK.search(text))
    exp_hits = _EXPERIMENTAL.findall(text)
    exp_n = len(exp_hits)
    narrative = bool(_NARRATIVE.search(text))
    title_both = bool(_TITLE_BOTH.search(title))

    reasons: list[str] = []
    score = 0
    if tool_named:
        score += 2
        reasons.append("tool_named")
    if tool_used:
        score += 3
        reasons.append("tool_used_to_predict")
    if benchmark:
        score -= 4
        reasons.append("benchmark_against_tool")
    if exp_n >= 2:
        score += 2
        reasons.append(f"experimental_cues:{exp_n}")
    elif exp_n == 1:
        score += 1
        reasons.append("experimental_cue")
    if narrative:
        score += 2
        reasons.append("predict_then_test_narrative")
    if title_both:
        score += 1
        reasons.append("title_silico_and_vitro")

    confidence = "none"
    if benchmark:
        confidence = "none"
    elif tool_used and exp_n >= 1 and (narrative or title_both or exp_n >= 2):
        confidence = "high"
    elif tool_used and exp_n >= 1:
        confidence = "high"
    elif tool_named and exp_n >= 1 and (narrative or title_both):
        confidence = "medium"
    elif tool_named and tool_used and exp_n == 0:
        confidence = "low"
    elif tool_named and exp_n >= 1:
        confidence = "medium"
    elif score >= 4 and not tool_named:
        # Strong silico→vitro narrative but XenoSite not named in title/abstract.
        confidence = "low"
        reasons.append("no_tool_name_in_abstract")

    return {
        "confidence": confidence,
        "score": score,
        "reasons": reasons,
        "tool_named": tool_named,
        "tool_used_to_predict": tool_used,
        "benchmark_against_tool": benchmark,
        "experimental_hits": exp_n,
        "predict_then_test_narrative": narrative,
        "title_silico_and_vitro": title_both,
    }


def is_predict_then_test_candidate(
    paper: dict[str, Any], *, min_confidence: str = "medium"
) -> bool:
    """Return True if confidence meets ``min_confidence`` (``high``|``medium``|``low``)."""
    order = {"none": 0, "low": 1, "medium": 2, "high": 3}
    result = score_predict_then_test(paper)
    return order.get(result["confidence"], 0) >= order.get(min_confidence, 2)
