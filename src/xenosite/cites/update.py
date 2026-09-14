"""Incremental OpenAlex citation updates with diff-minimizing writes."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from xenosite.cites.openalex import OpenAlexClient, work_record
from xenosite.cites.seeds import load_seeds

# Updated on every OpenAlex pull; rewriting them churns weekly diffs.
_VOLATILE_FIELDS = frozenset({"cited_by_count", "cited_by_api_url"})


def _dumps_jsonl_row(row: dict[str, Any]) -> str:
    # Match historical dumps so unchanged rows stay byte-identical.
    return json.dumps(row, sort_keys=True)


def _dumps_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_text_if_changed(path: Path, text: str) -> bool:
    """Write ``text`` only when it differs from the on-disk file. Return True if written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def write_json_if_changed(path: Path, payload: Any) -> bool:
    return write_text_if_changed(path, _dumps_json(payload))


def write_jsonl_if_changed(path: Path, rows: list[dict[str, Any]]) -> bool:
    text = "".join(_dumps_jsonl_row(row) + "\n" for row in rows)
    return write_text_if_changed(path, text)


def _records_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return _dumps_jsonl_row(a) == _dumps_jsonl_row(b)


def merge_record(
    prior: dict[str, Any],
    incoming: dict[str, Any],
    *,
    update_volatile: bool = False,
) -> dict[str, Any]:
    """Update ``prior`` with ``incoming``, preserving prior keys unless improved.

    By default skips volatile fields (citation counts) to avoid weekly churn.
    """
    merged = dict(prior)
    for key, value in incoming.items():
        if key in _VOLATILE_FIELDS and not update_volatile:
            continue
        if key.startswith("cites_seed"):
            if merged.get(key) != value:
                merged[key] = value
            continue
        if value in (None, "", [], {}):
            continue
        # Keep existing non-empty abstract/doi/title unless incoming fills a gap.
        if key in {"abstract", "doi", "title", "venue"} and merged.get(key):
            continue
        if key == "referenced_works" and merged.get("referenced_works"):
            continue
        if key == "authors" and merged.get("authors"):
            continue
        if merged.get(key) != value:
            merged[key] = value
    if update_volatile:
        for key in _VOLATILE_FIELDS:
            if key in incoming and merged.get(key) != incoming.get(key):
                merged[key] = incoming[key]
    return prior if _records_equal(merged, prior) else merged


def merge_citing_records(
    existing: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
    *,
    update_volatile: bool = False,
) -> tuple[list[dict[str, Any]], int, int]:
    """Merge citing works by ``openalex_id`` with stable ordering.

    Existing rows keep their file order. New IDs are appended, sorted by
    ``(year, title, openalex_id)``. Existing rows are replaced only when the
    merged record differs.

    Returns ``(merged_rows, n_added, n_updated)``.
    """
    by_id: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for row in existing:
        oid = str(row.get("openalex_id") or "")
        if not oid:
            continue
        if oid not in by_id:
            order.append(oid)
        by_id[oid] = row

    n_added = 0
    n_updated = 0
    new_ids: list[str] = []
    for row in incoming:
        oid = str(row.get("openalex_id") or "")
        if not oid:
            continue
        prior = by_id.get(oid)
        if prior is None:
            by_id[oid] = row
            new_ids.append(oid)
            n_added += 1
            continue
        merged = merge_record(prior, row, update_volatile=update_volatile)
        if not _records_equal(merged, prior):
            by_id[oid] = merged
            n_updated += 1

    new_ids_sorted = sorted(
        new_ids,
        key=lambda oid: (
            by_id[oid].get("year") or 0,
            str(by_id[oid].get("title") or ""),
            oid,
        ),
    )
    rows = [by_id[oid] for oid in order + new_ids_sorted]
    return rows, n_added, n_updated


def resolve_since_date(
    *,
    since: str | None,
    full: bool,
    manifest_path: Path,
    overlap_days: int,
) -> str | None:
    """Return OpenAlex ``from_created_date`` string, or ``None`` for a full scan."""
    if full:
        return None
    if since:
        return since
    if not manifest_path.exists():
        return None
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    last = payload.get("last_success_utc")
    if not last:
        return None
    try:
        last_dt = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
    except ValueError:
        return None
    start = last_dt.astimezone(UTC) - timedelta(days=overlap_days)
    return start.date().isoformat()


def update_citations(
    *,
    artifacts_dir: Path,
    mailto: str = "swamidass@gmail.com",
    since: str | None = None,
    full: bool = False,
    overlap_days: int = 14,
    update_volatile: bool = False,
) -> dict[str, Any]:
    """Refresh seed metadata and incrementally merge new citing works."""
    openalex_dir = artifacts_dir / "openalex"
    seeds_dir = openalex_dir / "seeds"
    citing_dir = openalex_dir / "citing"
    manifest_path = openalex_dir / "update_manifest.json"
    seeds_dir.mkdir(parents=True, exist_ok=True)
    citing_dir.mkdir(parents=True, exist_ok=True)

    since_date = resolve_since_date(
        since=since,
        full=full,
        manifest_path=manifest_path,
        overlap_days=overlap_days,
    )
    # First clone / empty store: do a full citing scan.
    if since_date is None and not full:
        any_citing = any(citing_dir.glob("*.jsonl"))
        if not any_citing:
            since_date = None  # full
            full = True

    started = datetime.now(UTC)
    per_seed: dict[str, Any] = {}
    total_added = 0
    total_updated = 0
    files_written = 0

    with OpenAlexClient(mailto=mailto) as client:
        for seed in load_seeds():
            print(f"[update] {seed.id}: resolve DOI {seed.normalized_doi()}", flush=True)
            raw = client.work_by_doi(seed.normalized_doi())
            record = work_record(raw)
            record["seed_id"] = seed.id
            record["seed_tags"] = list(seed.tags)
            record["seed_notes"] = seed.notes
            seed_path = seeds_dir / f"{seed.id}.json"
            if seed_path.exists():
                prior_payload = json.loads(seed_path.read_text(encoding="utf-8"))
                prior_seed = prior_payload.get("seed")
                if isinstance(prior_seed, dict):
                    record = merge_record(
                        prior_seed,
                        record,
                        update_volatile=update_volatile or full,
                    )
            seed_payload = {"seed": record, "raw_openalex_id": raw.get("id")}
            if write_json_if_changed(seed_path, seed_payload):
                files_written += 1

            citing_path = citing_dir / f"{seed.id}.jsonl"
            existing = _read_jsonl(citing_path)
            openalex_id = str(record.get("openalex_id") or "")
            print(
                f"[update] {seed.id}: fetch citing"
                + (f" since {since_date}" if since_date else " (full)"),
                flush=True,
            )
            incoming: list[dict[str, Any]] = []
            for work in client.iter_citing_works(openalex_id, from_created_date=since_date):
                row = work_record(work)
                row["cites_seed_id"] = seed.id
                row["cites_seed_openalex_id"] = openalex_id
                row["cites_seed_doi"] = record.get("doi")
                incoming.append(row)
            merged, n_added, n_updated = merge_citing_records(
                existing, incoming, update_volatile=update_volatile or full
            )
            if write_jsonl_if_changed(citing_path, merged):
                files_written += 1
            total_added += n_added
            total_updated += n_updated
            per_seed[seed.id] = {
                "n_citing": len(merged),
                "n_fetched": len(incoming),
                "n_added": n_added,
                "n_updated": n_updated,
                "n_existing": len(existing),
            }
            print(
                f"[update] {seed.id}: existing={len(existing)} fetched={len(incoming)} "
                f"added={n_added} updated={n_updated} total={len(merged)}",
                flush=True,
            )

    finished = datetime.now(UTC)
    manifest = {
        "last_success_utc": finished.isoformat().replace("+00:00", "Z"),
        "started_utc": started.isoformat().replace("+00:00", "Z"),
        "since_created_date": since_date,
        "full_refresh": bool(full or since_date is None),
        "overlap_days": overlap_days,
        "update_volatile": update_volatile or full,
        "n_seeds": len(per_seed),
        "n_added_total": total_added,
        "n_updated_total": total_updated,
        "n_files_written": files_written,
        "seeds": per_seed,
    }
    # Manifest always records the run clock; that is intentional churn.
    write_json_if_changed(manifest_path, manifest)
    print(
        f"[update] done; added={total_added} updated={total_updated} files_written={files_written}",
        flush=True,
    )
    return manifest
