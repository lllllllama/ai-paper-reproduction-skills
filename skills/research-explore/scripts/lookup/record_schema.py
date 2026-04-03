"""Lookup record schema helpers."""

from __future__ import annotations

from typing import Any, Dict


EVIDENCE_CLASS_ALIASES = {
    "external-provider": "external_provider",
    "parsed-locator": "parsed_locator",
    "repo-local-extracted": "repo_local_extracted",
    "seed-only": "seed_only",
}

EVIDENCE_CLASS_PRIORITY = {
    "seed_only": 0,
    "repo_local_extracted": 1,
    "parsed_locator": 2,
    "external_provider": 3,
}

DEFAULT_RECORD_FIELDS = {
    "source_type": "web",
    "provider_type": "seed",
    "locator_type": "seed",
    "raw_locator": "",
    "normalized_id": "",
    "title": "",
    "summary": "",
    "url": "",
    "authors": [],
    "year": None,
    "venue": "",
    "repo_full_name": "",
    "doi": "",
    "arxiv_id": "",
    "evidence_class": "seed_only",
    "evidence_weight": 0.2,
    "resolved_at": "",
    "cache_hit": False,
    "parse_status": "seed-only",
    "fetch_status": "seed-only",
    "provider_metadata": {},
    "source_repo": "",
    "source_file": "",
    "source_symbol": "",
    "origins": [],
    "extracted_from_repo_paths": [],
    "selection_hints": [],
}


def normalize_evidence_class(value: Any, default: str = "seed_only") -> str:
    text = str(value or "").strip().lower().replace("-", "_")
    text = EVIDENCE_CLASS_ALIASES.get(text, text)
    if text in EVIDENCE_CLASS_PRIORITY:
        return text
    return default


def evidence_weight_for_class(evidence_class: Any, parse_status: Any = "") -> float:
    normalized = normalize_evidence_class(evidence_class)
    status = str(parse_status or "").strip().lower()
    if normalized == "external_provider":
        return 1.0 if status in {"resolved", "network-fetched"} else 0.9
    if normalized == "parsed_locator":
        return 0.65
    if normalized == "repo_local_extracted":
        return 0.45
    return 0.2


def metadata_completeness(record: Dict[str, Any]) -> int:
    score = 0
    for key in ("title", "summary", "url", "repo_full_name", "doi", "arxiv_id", "venue"):
        if record.get(key):
            score += 1
    authors = record.get("authors")
    if isinstance(authors, list) and authors:
        score += 1
    if record.get("year"):
        score += 1
    return score


def normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {**DEFAULT_RECORD_FIELDS, **record}
    normalized["evidence_class"] = normalize_evidence_class(normalized.get("evidence_class"))
    normalized["evidence_weight"] = round(
        float(
            normalized.get("evidence_weight")
            or evidence_weight_for_class(normalized["evidence_class"], normalized.get("parse_status"))
        ),
        4,
    )
    normalized["authors"] = [str(item) for item in normalized.get("authors", []) if str(item).strip()]
    normalized["origins"] = [str(item) for item in normalized.get("origins", []) if str(item).strip()]
    normalized["extracted_from_repo_paths"] = [
        str(item).replace("\\", "/")
        for item in normalized.get("extracted_from_repo_paths", [])
        if str(item).strip()
    ]
    normalized["selection_hints"] = [str(item) for item in normalized.get("selection_hints", []) if str(item).strip()]
    return normalized


def record_priority(record: Dict[str, Any]) -> tuple[int, int]:
    normalized = normalize_record(record)
    return (
        EVIDENCE_CLASS_PRIORITY.get(normalized["evidence_class"], 0),
        metadata_completeness(normalized),
    )
