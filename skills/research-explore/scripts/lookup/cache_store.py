"""Cache/index helpers for source records."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .normalizers import slugify, stable_digest, stable_filename
from .record_schema import normalize_record, record_priority


def _normalized_id_from_index_item(item: Dict[str, Any]) -> str:
    if item.get("normalized_id"):
        return str(item.get("normalized_id"))
    provider_type = str(item.get("provider_type") or "seed")
    identifier = str(item.get("provider_identifier") or item.get("source_url") or item.get("query") or "")
    return f"{provider_type}:{identifier}".strip(":")


def load_cache_index(sources_dir: Path) -> Dict[str, Any]:
    index_path = sources_dir / "index.json"
    if not index_path.exists():
        return {
            "schema_version": "2.0",
            "mode": "free-first-cache-first",
            "records_dir": "sources/records",
            "records": [],
            "record_lookup": {},
        }
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    payload["record_lookup"] = {
        _normalized_id_from_index_item(item): dict(item)
        for item in records
        if _normalized_id_from_index_item(item)
    }
    return payload


def _merge_lists(left: Iterable[Any], right: Iterable[Any]) -> List[Any]:
    merged: List[Any] = []
    for item in list(left) + list(right):
        if item not in merged and item not in ("", None, []):
            merged.append(item)
    return merged


def _prefer_value(existing: Any, incoming: Any) -> Any:
    if incoming not in ("", None, [], {}):
        return incoming
    return existing


def merge_records(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    normalized_existing = normalize_record(existing)
    normalized_incoming = normalize_record(incoming)
    if record_priority(normalized_incoming) >= record_priority(normalized_existing):
        primary, secondary = normalized_incoming, normalized_existing
    else:
        primary, secondary = normalized_existing, normalized_incoming
    merged = dict(primary)
    for key in (
        "title",
        "summary",
        "url",
        "venue",
        "repo_full_name",
        "doi",
        "arxiv_id",
        "source_repo",
        "source_file",
        "source_symbol",
    ):
        merged[key] = _prefer_value(secondary.get(key), primary.get(key))
    merged["authors"] = _merge_lists(secondary.get("authors", []), primary.get("authors", []))
    merged["origins"] = _merge_lists(secondary.get("origins", []), primary.get("origins", []))
    merged["extracted_from_repo_paths"] = _merge_lists(
        secondary.get("extracted_from_repo_paths", []),
        primary.get("extracted_from_repo_paths", []),
    )
    merged["selection_hints"] = _merge_lists(secondary.get("selection_hints", []), primary.get("selection_hints", []))
    merged["provider_metadata"] = {**secondary.get("provider_metadata", {}), **primary.get("provider_metadata", {})}
    return normalize_record(merged)


def store_records(sources_dir: Path, records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    sources_dir.mkdir(parents=True, exist_ok=True)
    records_dir = sources_dir / "records"
    records_dir.mkdir(parents=True, exist_ok=True)

    existing_index = load_cache_index(sources_dir)
    existing_lookup = existing_index.get("record_lookup", {})
    stored_by_id: Dict[str, Dict[str, Any]] = {}
    cache_hits = 0
    cache_misses = 0
    merge_upgrades = 0

    for raw_record in records:
        record = normalize_record(raw_record)
        normalized_id = str(record.get("normalized_id") or "")
        if not normalized_id:
            identity = {
                "source_type": record.get("source_type"),
                "provider_type": record.get("provider_type"),
                "locator_type": record.get("locator_type"),
                "raw_locator": record.get("raw_locator"),
                "url": record.get("url"),
                "title": record.get("title"),
            }
            normalized_id = f"seed:{stable_digest(identity)[:16]}"
            record["normalized_id"] = normalized_id
        if normalized_id in stored_by_id:
            stored_by_id[normalized_id] = merge_records(stored_by_id[normalized_id], record)
            continue
        existing = existing_lookup.get(normalized_id)
        if existing:
            cache_hits += 1
            existing_rel = str(existing.get("artifact_path") or "")
            existing_path = None
            if existing_rel.startswith("sources/"):
                existing_path = sources_dir / Path(existing_rel).relative_to("sources")
            existing_payload = dict(existing)
            if existing_path and existing_path.exists():
                existing_payload = json.loads(existing_path.read_text(encoding="utf-8"))
            merged = merge_records(existing_payload, record)
            if record_priority(merged) > record_priority(normalize_record(existing_payload)):
                merge_upgrades += 1
            merged["cache_hit"] = True
            stored_by_id[normalized_id] = merged
        else:
            cache_misses += 1
            record["cache_hit"] = False
            stored_by_id[normalized_id] = record

    timestamp = datetime.now(timezone.utc).isoformat()
    stored_records: List[Dict[str, Any]] = []
    index_records: List[Dict[str, Any]] = []
    for normalized_id in sorted(stored_by_id):
        record = normalize_record(stored_by_id[normalized_id])
        if not record.get("resolved_at"):
            record["resolved_at"] = timestamp
        digest = stable_digest(
            {
                "normalized_id": normalized_id,
                "provider_type": record.get("provider_type"),
                "source_type": record.get("source_type"),
            }
        )
        source_id = record.get("source_id") or f"{record.get('source_type', 'source')}:{digest[:8]}"
        record["source_id"] = source_id
        slug = slugify(record.get("title") or normalized_id)
        filename = stable_filename(str(record.get("source_type") or "source"), slug, digest)
        artifact_path = records_dir / filename
        record["artifact_path"] = f"sources/records/{filename}"
        record["artifact_abspath"] = str(artifact_path)
        record["digest"] = digest
        artifact_path.write_text(
            json.dumps({"schema_version": "2.0", **record}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        stored_records.append(record)
        index_records.append(
            {
                "source_id": source_id,
                "source_type": record.get("source_type"),
                "provider_type": record.get("provider_type"),
                "locator_type": record.get("locator_type"),
                "raw_locator": record.get("raw_locator"),
                "normalized_id": normalized_id,
                "title": record.get("title"),
                "url": record.get("url"),
                "repo_full_name": record.get("repo_full_name"),
                "doi": record.get("doi"),
                "arxiv_id": record.get("arxiv_id"),
                "evidence_class": record.get("evidence_class"),
                "evidence_weight": record.get("evidence_weight"),
                "parse_status": record.get("parse_status"),
                "cache_hit": record.get("cache_hit"),
                "artifact_path": record.get("artifact_path"),
                "source_repo": record.get("source_repo"),
                "source_file": record.get("source_file"),
                "source_symbol": record.get("source_symbol"),
                "resolved_at": record.get("resolved_at"),
            }
        )

    index_payload = {
        "schema_version": "2.0",
        "mode": "free-first-cache-first",
        "records_dir": "sources/records",
        "records": index_records,
        "stats": {
            "record_count": len(index_records),
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "merge_upgrades": merge_upgrades,
        },
    }
    index_path = sources_dir / "index.json"
    index_path.write_text(json.dumps(index_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "index_path": str(index_path),
        "records_dir": str(records_dir),
        "records": stored_records,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "merge_upgrades": merge_upgrades,
    }
