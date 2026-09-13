"""Curated seed papers whose citations we study."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class SeedPaper:
    """One XenoSite-related paper used as a citation seed."""

    id: str
    doi: str
    title: str
    year: int
    notes: str = ""

    def normalized_doi(self) -> str:
        """Return DOI without a leading ``https://doi.org/`` prefix.

        >>> SeedPaper("x", "https://doi.org/10.1/abc", "t", 2020).normalized_doi()
        '10.1/abc'
        """
        doi = self.doi.strip()
        for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
            if doi.lower().startswith(prefix):
                return doi[len(prefix) :].strip()
        return doi


def _parse_seeds(raw: Any) -> tuple[SeedPaper, ...]:
    if not isinstance(raw, dict):
        raise TypeError("seeds.yaml root must be a mapping")
    papers = raw.get("papers")
    if not isinstance(papers, list):
        raise TypeError("seeds.yaml must contain a 'papers' list")
    out: list[SeedPaper] = []
    seen: set[str] = set()
    for item in papers:
        if not isinstance(item, dict):
            raise TypeError("each paper entry must be a mapping")
        paper = SeedPaper(
            id=str(item["id"]),
            doi=str(item["doi"]),
            title=str(item["title"]),
            year=int(item["year"]),
            notes=str(item.get("notes", "")),
        )
        if paper.id in seen:
            raise ValueError(f"duplicate seed id: {paper.id}")
        seen.add(paper.id)
        out.append(paper)
    return tuple(out)


@lru_cache(maxsize=1)
def load_seeds(path: Path | None = None) -> tuple[SeedPaper, ...]:
    """Load curated seed papers from YAML.

    Defaults to the packaged ``seeds.yaml``. Pass ``path`` to override
    (e.g. a working copy under ``data/``).
    """
    if path is None:
        text = resources.files("xenosite.cites").joinpath("seeds.yaml").read_text(encoding="utf-8")
    else:
        text = path.read_text(encoding="utf-8")
    return _parse_seeds(yaml.safe_load(text))
