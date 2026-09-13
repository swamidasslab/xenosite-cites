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

# Computational / modeling language when the tool is not named in the abstract.
_MODELING = re.compile(
    r"\b("
    r"computational|in\s+silico|modeling|modelling|model(?:ing|ling)\s+approach|"
    r"docking|predict\w+|simulation"
    r")\b",
    re.I,
)

# Explicit "computational and experimental" pairing (common lab phrasing).
_COMP_AND_EXP = re.compile(
    r"("
    r"computational\s+and\s+experimental|"
    r"experimental\s+and\s+computational|"
    r"modeling\s+and\s+(reaction\s+)?kinetics?|"
    r"kinetic\s+and\s+modeling|"
    r"in\s+vitro\s+studies.{0,40}modeling|"
    r"modeling\s+approaches.{0,40}in\s+vitro|"
    r"experimental\s+tools.{0,20}computational|"
    r"computational\s+tools.{0,20}experimental"
    r")",
    re.I | re.S,
)

# Keep inferred (no tool name) hits on metabolism/bioactivation applications.
_METAB_CONTEXT = re.compile(
    r"\b("
    r"bioactivation|metaboli[sz]|site\s+of\s+metabolism|n[- ]?dealkylation|"
    r"reactive\s+metabolite|cytochrome|cyp\d*|microsom\w*|hepatotox|"
    r"xenobiotic|lamisil|terbinafine"
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
    r"(in\s+silico|predict\w*|model(?:ing|ling)).{0,100}"
    r"(in\s+vitro|in\s+vivo|microsom)|"
    r"(in\s+vitro|in\s+vivo).{0,60}(in\s+silico|predict\w*|model(?:ing|ling))"
    r")",
    re.I | re.S,
)

_TITLE_BOTH = re.compile(
    r"("
    r"in\s+silico.{0,40}(in\s+vitro|in\s+vivo)|"
    r"(in\s+vitro|in\s+vivo).{0,40}in\s+silico|"
    r"computational\s+and\s+experimental|"
    r"experimental\s+and\s+computational"
    r")",
    re.I | re.S,
)


def _blob(paper: dict[str, Any]) -> tuple[str, str, str]:
    title = str(paper.get("title") or "")
    abstract = str(paper.get("abstract") or "")
    return title, abstract, f"{title}\n{abstract}"


def _seed_links(paper: dict[str, Any]) -> list[str]:
    cites = list(paper.get("cites_seed_ids") or [])
    refs = list(paper.get("references_seed_ids") or [])
    return sorted({str(x) for x in cites + refs if x})


def score_predict_then_test(paper: dict[str, Any]) -> dict[str, Any]:
    """Score whether a paper uses a XenoSite-family tool then tests experimentally.

    Confidence:
    - ``high``: explicit tool use + experiment, **or** cites a XenoSite-family seed and
      pairs modeling/computational language with experimental testing (lab-style papers
      often omit the product name from the abstract).
    - ``medium``: weaker but consistent signals (tool named + experiment, or seed citation
      + computational/experimental pairing without a strong narrative).
    - ``low``: incomplete signals.
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
    modeling = bool(_MODELING.search(text))
    comp_and_exp = bool(_COMP_AND_EXP.search(text))
    metab_context = bool(_METAB_CONTEXT.search(text))
    seed_ids = _seed_links(paper)
    cites_seed = bool(seed_ids)

    reasons: list[str] = []
    score = 0
    if tool_named:
        score += 2
        reasons.append("tool_named")
    if tool_used:
        score += 3
        reasons.append("tool_used_to_predict")
    if cites_seed:
        score += 2
        reasons.append(f"cites_seed:{','.join(seed_ids[:4])}")
    if benchmark:
        score -= 4
        reasons.append("benchmark_against_tool")
    if exp_n >= 2:
        score += 2
        reasons.append(f"experimental_cues:{exp_n}")
    elif exp_n == 1:
        score += 1
        reasons.append("experimental_cue")
    if modeling:
        score += 1
        reasons.append("modeling_language")
    if comp_and_exp:
        score += 2
        reasons.append("computational_and_experimental")
    if metab_context:
        score += 1
        reasons.append("metabolism_context")
    if narrative:
        score += 2
        reasons.append("predict_then_test_narrative")
    if title_both:
        score += 1
        reasons.append("title_silico_and_vitro")

    # Inferred tool use: cites a XenoSite-family seed and frames the work as
    # computational+experimental metabolism/bioactivation (tool name often omitted).
    inferred_use = bool(
        cites_seed
        and metab_context
        and (comp_and_exp or title_both)
        and (exp_n >= 1 or comp_and_exp or title_both)
    )

    confidence = "none"
    if benchmark:
        confidence = "none"
    elif tool_used and exp_n >= 1:
        confidence = "high"
    elif inferred_use:
        confidence = "high"
        reasons.append("tool_inferred_from_seed_citation")
    elif cites_seed and metab_context and modeling and exp_n >= 2:
        confidence = "medium"
        reasons.append("tool_inferred_from_seed_citation")
    elif tool_named and exp_n >= 1 and (narrative or title_both):
        confidence = "medium"
    elif tool_named and tool_used and exp_n == 0:
        confidence = "low"
    elif tool_named and exp_n >= 1:
        confidence = "medium"
    elif score >= 4 and not tool_named and not cites_seed:
        confidence = "low"
        reasons.append("no_tool_name_in_abstract")
    elif cites_seed and modeling and exp_n >= 1 and not tool_named:
        confidence = "low"
        reasons.append("no_tool_name_in_abstract")

    return {
        "confidence": confidence,
        "score": score,
        "reasons": reasons,
        "tool_named": tool_named,
        "tool_used_to_predict": tool_used,
        "tool_inferred_from_seed_citation": bool(
            inferred_use or ("tool_inferred_from_seed_citation" in reasons)
        ),
        "cites_seed_ids": seed_ids,
        "benchmark_against_tool": benchmark,
        "experimental_hits": exp_n,
        "predict_then_test_narrative": narrative,
        "title_silico_and_vitro": title_both,
        "computational_and_experimental": comp_and_exp,
        "metabolism_context": metab_context,
    }
