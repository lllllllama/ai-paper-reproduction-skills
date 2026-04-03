"""Machine-readable source support artifacts for downstream passes."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Sequence

from .record_schema import normalize_evidence_class


def _tokenize(value: Any) -> List[str]:
    return [token for token in re.split(r"[^a-z0-9]+", str(value or "").lower()) if len(token) > 2]


def _record_haystack(record: Dict[str, Any]) -> str:
    return " ".join(
        [
            str(record.get("title") or ""),
            str(record.get("summary") or ""),
            str(record.get("url") or ""),
            str(record.get("repo_full_name") or ""),
            str(record.get("doi") or ""),
            str(record.get("arxiv_id") or ""),
            str(record.get("source_repo") or ""),
            str(record.get("source_file") or ""),
            str(record.get("source_symbol") or ""),
        ]
    ).lower()


def _match_records(tokens: Sequence[str], records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    matches: List[tuple[int, float, Dict[str, Any]]] = []
    for record in records:
        haystack = _record_haystack(record)
        score = sum(1 for token in tokens if token in haystack)
        if score > 0:
            matches.append((score, float(record.get("evidence_weight") or 0.0), record))
    matches.sort(key=lambda item: (-item[0], -item[1], item[2].get("source_id", "")))
    return [record for _score, _weight, record in matches[:6]]


def build_source_support(
    campaign: Dict[str, Any],
    records: Sequence[Dict[str, Any]],
    repo_local_extractions: Sequence[Dict[str, Any]],
    cache_stats: Dict[str, Any],
) -> Dict[str, Any]:
    by_evidence_class: Dict[str, List[str]] = {}
    by_type: Dict[str, List[str]] = {}
    for item in records:
        evidence = normalize_evidence_class(item.get("evidence_class"))
        by_evidence_class.setdefault(evidence, []).append(str(item.get("source_id")))
        source_type = str(item.get("source_type") or "unknown")
        by_type.setdefault(source_type, []).append(str(item.get("source_id")))

    support_index_by_candidate_idea: Dict[str, Dict[str, Any]] = {}
    support_index_by_target_component: Dict[str, Dict[str, Any]] = {}
    for idea in campaign.get("candidate_ideas", []):
        idea_id = str(idea.get("id") or "idea")
        tokens = _tokenize(idea.get("summary")) + _tokenize(idea.get("target_component")) + _tokenize(idea.get("change_scope"))
        matched = _match_records(tokens, records)
        support_index_by_candidate_idea[idea_id] = {
            "matched_source_ids": [item.get("source_id") for item in matched],
            "matched_external_source_ids": [
                item.get("source_id")
                for item in matched
                if normalize_evidence_class(item.get("evidence_class")) == "external_provider"
            ],
            "matched_repo_local_source_ids": [
                item.get("source_id")
                for item in matched
                if normalize_evidence_class(item.get("evidence_class")) == "repo_local_extracted"
            ],
            "matched_parsed_locator_ids": [
                item.get("source_id")
                for item in matched
                if normalize_evidence_class(item.get("evidence_class")) == "parsed_locator"
            ],
        }
        component = str(idea.get("target_component") or "unspecified")
        support_index_by_target_component.setdefault(component, {"matched_source_ids": []})
        for source_id in support_index_by_candidate_idea[idea_id]["matched_source_ids"]:
            if source_id not in support_index_by_target_component[component]["matched_source_ids"]:
                support_index_by_target_component[component]["matched_source_ids"].append(source_id)

    return {
        "schema_version": "1.0",
        "records": list(records),
        "records_by_evidence_class": by_evidence_class,
        "records_by_type": by_type,
        "support_index_by_candidate_idea": support_index_by_candidate_idea,
        "support_index_by_target_component": support_index_by_target_component,
        "repo_local_extractions": list(repo_local_extractions),
        "cache_stats": cache_stats,
    }


def write_source_support(analysis_output_dir: Path, support_bundle: Dict[str, Any]) -> Path:
    path = analysis_output_dir / "SOURCE_SUPPORT.json"
    path.write_text(json.dumps(support_bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
