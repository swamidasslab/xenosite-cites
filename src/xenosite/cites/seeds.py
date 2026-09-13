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
    tags: tuple[str, ...] = ()

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
    seen_ids: set[str] = set()
    seen_dois: set[str] = set()
    for item in papers:
        if not isinstance(item, dict):
            raise TypeError("each paper entry must be a mapping")
        tags_raw = item.get("tags", [])
        if tags_raw is None:
            tags: tuple[str, ...] = ()
        elif isinstance(tags_raw, list):
            tags = tuple(str(t) for t in tags_raw)
        else:
            raise TypeError("tags must be a list of strings")
        paper = SeedPaper(
            id=str(item["id"]),
            doi=str(item["doi"]),
            title=str(item["title"]),
            year=int(item["year"]),
            notes=str(item.get("notes", "")),
            tags=tags,
        )
        if paper.id in seen_ids:
            raise ValueError(f"duplicate seed id: {paper.id}")
        doi_key = paper.normalized_doi().lower()
        if doi_key in seen_dois:
            raise ValueError(f"duplicate seed DOI: {paper.doi}")
        seen_ids.add(paper.id)
        seen_dois.add(doi_key)
        out.append(paper)
    return tuple(out)


@lru_cache(maxsize=8)
def load_seeds(path: str | None = None) -> tuple[SeedPaper, ...]:
    """Load curated seed papers from YAML.

    Defaults to the packaged ``seeds.yaml``. Pass a filesystem path string to
    override (e.g. a working copy under ``data/``).
    """
    if path is None:
        text = resources.files("xenosite.cites").joinpath("seeds.yaml").read_text(encoding="utf-8")
    else:
        text = Path(path).read_text(encoding="utf-8")
    return _parse_seeds(yaml.safe_load(text))
