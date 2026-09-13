"""Heuristic labels: experimental vs computational vs review."""

from __future__ import annotations

import re
from typing import Any

_REVIEW_TYPE = {"review", "editorial", "reference-entry"}
_REVIEW_TITLE = re.compile(
    r"\b(review|overview|perspective|minireview|mini-review|survey|state of the art)\b",
    re.I,
)
_COMP_PAT = re.compile(
    r"\b("
    r"in\s*silico|computational|cheminformat\w*|qsar|qspr|machine\s*learning|"
    r"deep\s*learning|neural\s*network|docking|virtual\s*screen\w*|"
    r"molecular\s*dynam\w*|simulation|predict\w*\s+model|graph\s*neural|"
    r"descriptor|fingerprint|algorithm|software|web\s*server|openalex|"
    r"artificial\s*intelligence|\bai\b|transformer|random\s*forest|"
    r"support\s*vector|ligand[- ]based|structure[- ]based"
    r")\b",
    re.I,
)
_EXP_PAT = re.compile(
    r"\b("
    r"in\s*vitro|in\s*vivo|microsom\w*|hepatocyte|incubat\w*|assay|"
    r"hplc|lc[- ]?ms|nmr|crystall\w*|synthesi[sz]\w*|metabolite\s+identif\w*|"
    r"kinetic|enzyme\s+assay|clinical|patient|animal|rat|mice|mouse|"
    r"western\s*blot|immunohisto\w*|biopsy|pharmacokinet\w*|dosing|"
    r"experimentally|wet[- ]lab"
    r")\b",
    re.I,
)


def _text(paper: dict[str, Any]) -> str:
    parts = [
        str(paper.get("title") or ""),
        str(paper.get("abstract") or ""),
        str(paper.get("venue") or ""),
    ]
    return " ".join(parts)


def classify_paper(paper: dict[str, Any]) -> dict[str, Any]:
    """Return label and evidence scores for one paper.

    Labels: ``review``, ``computational``, ``experimental``, ``mixed``, ``unknown``.
    OpenAlex ``type`` is used as a strong prior for reviews.
    """
    text = _text(paper)
    oa_type = str(paper.get("type") or "").lower()
    review_hit = oa_type in _REVIEW_TYPE or bool(
        _REVIEW_TITLE.search(str(paper.get("title") or ""))
    )
    comp_hits = _COMP_PAT.findall(text)
    exp_hits = _EXP_PAT.findall(text)
    comp_n = len(comp_hits)
    exp_n = len(exp_hits)

    if review_hit and comp_n == 0 and exp_n == 0:
        label = "review"
    elif review_hit and (comp_n or exp_n):
        # Reviews that are clearly method-focused still count as review.
        label = "review"
    elif comp_n > 0 and exp_n > 0:
        label = "mixed"
    elif comp_n > 0:
        label = "computational"
    elif exp_n > 0:
        label = "experimental"
    else:
        label = "unknown"

    return {
        "label": label,
        "openalex_type": oa_type or None,
        "review_signal": review_hit,
        "computational_hits": comp_n,
        "experimental_hits": exp_n,
    }
