"""OpenAlex helpers for resolving works and citing papers."""

from __future__ import annotations

import json
import time
from typing import Any, Iterator
from urllib.parse import quote

import httpx

OPENALEX_API = "https://api.openalex.org"
DEFAULT_MAILTO = "swamidass@gmail.com"
USER_AGENT = f"xenosite-cites/0.1 (mailto:{DEFAULT_MAILTO})"


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str | None:
    """Rebuild abstract text from OpenAlex ``abstract_inverted_index``.

    >>> reconstruct_abstract({"Hello": [0], "world": [1]})
    'Hello world'
    >>> reconstruct_abstract(None) is None
    True
    """
    if not inverted_index:
        return None
    max_pos = max(pos for positions in inverted_index.values() for pos in positions)
    words = [""] * (max_pos + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    text = " ".join(words).strip()
    return text or None


def normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    value = doi.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if value.lower().startswith(prefix):
            value = value[len(prefix) :].strip()
            break
    return value or None


def author_names(authorships: list[dict[str, Any]] | None) -> list[str]:
    names: list[str] = []
    for authorship in authorships or []:
        author = authorship.get("author") or {}
        name = author.get("display_name")
        if name:
            names.append(str(name))
    return names


def venue_name(work: dict[str, Any]) -> str | None:
    primary = work.get("primary_location") or {}
    source = primary.get("source") or {}
    name = source.get("display_name")
    return str(name) if name else None


def work_record(work: dict[str, Any]) -> dict[str, Any]:
    """Normalize an OpenAlex work into a stable local record."""
    doi = normalize_doi(work.get("doi"))
    return {
        "openalex_id": work.get("id"),
        "doi": doi,
        "title": work.get("title") or work.get("display_name"),
        "year": work.get("publication_year"),
        "publication_date": work.get("publication_date"),
        "type": work.get("type"),
        "cited_by_count": work.get("cited_by_count"),
        "authors": author_names(work.get("authorships")),
        "venue": venue_name(work),
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
        "referenced_works": list(work.get("referenced_works") or []),
        "cited_by_api_url": work.get("cited_by_api_url"),
        "ids": work.get("ids") or {},
    }


class OpenAlexClient:
    """Thin OpenAlex Works API client with polite-pool identification."""

    def __init__(
        self,
        *,
        mailto: str = DEFAULT_MAILTO,
        timeout: float = 60.0,
        min_interval: float = 0.1,
        max_retries: int = 5,
    ) -> None:
        self.mailto = mailto
        self.min_interval = min_interval
        self.max_retries = max_retries
        self._last_request = 0.0
        self._client = httpx.Client(
            base_url=OPENALEX_API,
            headers={"User-Agent": f"xenosite-cites/0.1 (mailto:{mailto})"},
            timeout=timeout,
            follow_redirects=True,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> OpenAlexClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        query = dict(params or {})
        query.setdefault("mailto", self.mailto)
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            self._throttle()
            try:
                response = self._client.get(path, params=query)
                self._last_request = time.monotonic()
                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", "2"))
                    time.sleep(retry_after * (attempt + 1))
                    continue
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    raise TypeError(f"expected JSON object from OpenAlex, got {type(data)}")
                return data
            except (httpx.HTTPError, json.JSONDecodeError, TypeError) as exc:
                last_error = exc
                time.sleep(min(2**attempt, 30))
        assert last_error is not None
        raise last_error

    def work_by_doi(self, doi: str) -> dict[str, Any]:
        clean = normalize_doi(doi)
        if not clean:
            raise ValueError(f"invalid DOI: {doi!r}")
        return self._get(f"/works/doi:{quote(clean, safe='')}")

    def iter_citing_works(
        self,
        openalex_id: str,
        *,
        per_page: int = 200,
        from_created_date: str | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Yield works that cite ``openalex_id`` (full OpenAlex URL or short id).

        If ``from_created_date`` is set (``YYYY-MM-DD``), only works created in
        OpenAlex on/after that date are returned (useful for incremental updates).
        """
        short = openalex_id.rstrip("/").split("/")[-1]
        parts = [f"cites:{short}"]
        if from_created_date:
            parts.append(f"from_created_date:{from_created_date}")
        filt = ",".join(parts)
        cursor: str | None = "*"
        while cursor:
            data = self._get(
                "/works",
                {
                    "filter": filt,
                    "per_page": per_page,
                    "cursor": cursor,
                },
            )
            for work in data.get("results") or []:
                if isinstance(work, dict):
                    yield work
            next_cursor = (data.get("meta") or {}).get("next_cursor")
            cursor = next_cursor if isinstance(next_cursor, str) and next_cursor else None
