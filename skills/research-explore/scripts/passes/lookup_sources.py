"""Free-first, cache-first research lookup pass for research-explore."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from lookup import (
    build_source_support,
    detect_locator,
    ensure_http_url,
    extract_repo_local_seeds,
    store_records,
    write_source_inventory,
    write_source_support,
    write_sources_summary,
)
from lookup.normalizers import stable_digest
from lookup.providers import (
    resolve_arxiv_record,
    resolve_doi_record,
    resolve_github_record,
    resolve_optional_record,
    resolve_url_record,
)
from lookup.record_schema import normalize_record


def dedupe_preserving_order(items: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[str] = set()
    ordered: List[Dict[str, Any]] = []
    for item in items:
        key = stable_digest(item)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(dict(item))
    return ordered


def command_paths(command: str) -> List[str]:
    paths: List[str] = []
    for token in re.findall(r"[\w./\\-]+\.(?:py|ya?ml|json|toml|ini|csv|md)", command):
        cleaned = token.strip().strip("\"'").replace("\\", "/")
        if cleaned and cleaned not in paths:
            paths.append(cleaned)
    return paths


def collect_seed_records(
    campaign: Dict[str, Any],
    analysis_data: Dict[str, Any],
    code_plan: Dict[str, Any],
) -> List[Dict[str, Any]]:
    evaluation_source = campaign.get("evaluation_source", {})
    benchmark = campaign.get("benchmark")
    benchmark_name = benchmark.get("name") if isinstance(benchmark, dict) else benchmark
    records: List[Dict[str, Any]] = [
        {
            "kind": "benchmark",
            "title": str(benchmark_name or "frozen-benchmark"),
            "summary": f"Frozen benchmark for {campaign.get('task_family') or 'research campaign'}.",
            "query": str(benchmark_name or campaign.get("dataset") or campaign.get("task_family") or "benchmark"),
            "source_url": "",
            "source_repo": "",
            "source_file": "",
            "source_symbol": "",
            "origin": "seed_only",
        },
        {
            "kind": "evaluation",
            "title": str(evaluation_source.get("path") or "evaluation-source"),
            "summary": str(evaluation_source.get("command") or "Frozen evaluation source."),
            "query": str(evaluation_source.get("command") or evaluation_source.get("path") or "evaluation"),
            "source_url": "",
            "source_repo": "",
            "source_file": str(evaluation_source.get("path") or ""),
            "source_symbol": "",
            "origin": "seed_only",
        },
    ]
    for path in command_paths(str(evaluation_source.get("command") or "")):
        records.append(
            {
                "kind": "module",
                "title": path,
                "summary": "Path referenced by the frozen evaluation contract.",
                "query": path,
                "source_url": "",
                "source_repo": "",
                "source_file": path,
                "source_symbol": "",
                "origin": "seed_only",
            }
        )
    for item in campaign.get("sota_reference", []):
        records.append(
            {
                "kind": "paper" if item.get("source") else "benchmark",
                "title": str(item.get("name") or "provided-sota"),
                "summary": f"Frozen comparison entry for {item.get('metric') or 'metric'}.",
                "query": str(item.get("name") or item.get("source") or item.get("metric") or "sota"),
                "source_url": ensure_http_url(str(item.get("source") or "")) if item.get("source") else "",
                "source_repo": "",
                "source_file": "",
                "source_symbol": "",
                "origin": "seed_only",
            }
        )
    for item in campaign.get("candidate_ideas", []):
        records.append(
            {
                "kind": "query",
                "title": str(item.get("id") or item.get("summary") or "candidate-idea"),
                "summary": str(item.get("summary") or ""),
                "query": " ".join(
                    token
                    for token in [
                        str(campaign.get("task_family") or ""),
                        str(campaign.get("dataset") or ""),
                        str(item.get("target_component") or ""),
                        str(item.get("change_scope") or ""),
                        str(item.get("summary") or ""),
                    ]
                    if token
                ),
                "source_url": ensure_http_url(str(item.get("source") or "")) if item.get("source") else "",
                "source_repo": str(item.get("source_repo") or ""),
                "source_file": str(item.get("source_file") or ""),
                "source_symbol": str(item.get("source_symbol") or ""),
                "origin": "seed_only",
            }
        )
    for item in code_plan.get("source_repo_refs", []):
        records.append(
            {
                "kind": "repo",
                "title": str(item.get("repo") or "source-repo"),
                "summary": str(item.get("note") or "Source repository reference for exploratory adaptation."),
                "query": str(item.get("repo") or item.get("ref") or "repo"),
                "source_url": ensure_http_url(str(item.get("url") or "")) if item.get("url") else "",
                "source_repo": str(item.get("repo") or ""),
                "source_file": "",
                "source_symbol": "",
                "origin": "seed_only",
            }
        )
    for path in analysis_data.get("module_files", [])[:6]:
        records.append(
            {
                "kind": "module",
                "title": str(path),
                "summary": "Task-relevant module candidate from read-only repo analysis.",
                "query": str(path),
                "source_url": "",
                "source_repo": "",
                "source_file": str(path),
                "source_symbol": "",
                "origin": "seed_only",
            }
        )
    for path in analysis_data.get("metric_files", [])[:4]:
        records.append(
            {
                "kind": "module",
                "title": str(path),
                "summary": "Metric or evaluation-related file from read-only repo analysis.",
                "query": str(path),
                "source_url": "",
                "source_repo": "",
                "source_file": str(path),
                "source_symbol": "",
                "origin": "seed_only",
            }
        )
    lookup_config = campaign.get("research_lookup", {})
    if isinstance(lookup_config, dict):
        for item in lookup_config.get("seed_sources", []) or []:
            if not isinstance(item, dict):
                continue
            records.append(
                {
                    "kind": str(item.get("kind") or "paper"),
                    "title": str(item.get("title") or item.get("name") or "seed-source"),
                    "summary": str(item.get("summary") or item.get("notes") or ""),
                    "query": str(item.get("query") or item.get("title") or ""),
                    "source_url": ensure_http_url(str(item.get("url") or item.get("source") or "")) if item.get("url") or item.get("source") else "",
                    "source_repo": str(item.get("source_repo") or item.get("repo") or ""),
                    "source_file": str(item.get("source_file") or item.get("file") or ""),
                    "source_symbol": str(item.get("source_symbol") or item.get("symbol") or ""),
                    "origin": "seed_only",
                }
            )
        for query in lookup_config.get("queries", []) or []:
            if not query:
                continue
            records.append(
                {
                    "kind": "query",
                    "title": str(query),
                    "summary": "Explicit research lookup query provided by the campaign.",
                    "query": str(query),
                    "source_url": ensure_http_url(str(query)),
                    "source_repo": "",
                    "source_file": "",
                    "source_symbol": "",
                    "origin": "seed_only",
                }
            )
    return dedupe_preserving_order(records)


def candidate_locators(raw: Dict[str, Any]) -> List[str]:
    locators: List[str] = []
    for value in [
        raw.get("raw_locator"),
        raw.get("source_url"),
        raw.get("query"),
        raw.get("title"),
    ]:
        text = str(value or "").strip()
        if text and text not in locators:
            locators.append(text)
    return locators


def resolve_provider_record(raw: Dict[str, Any], lookup_config: Dict[str, Any]) -> Dict[str, Any]:
    locator_info: Optional[Dict[str, Any]] = None
    for locator in candidate_locators(raw):
        locator_info = detect_locator(locator)
        if locator_info:
            break
    if locator_info:
        optional_record = resolve_optional_record(locator_info, lookup_config)
        resolved = optional_record or {}
        if not resolved:
            provider_type = locator_info.get("provider_type")
            if provider_type == "github":
                resolved = resolve_github_record(locator_info)
            elif provider_type == "arxiv":
                resolved = resolve_arxiv_record(locator_info)
            elif provider_type == "doi":
                resolved = resolve_doi_record(locator_info)
            elif provider_type == "url":
                resolved = resolve_url_record(locator_info)
            else:
                resolved = {}
        origin = str(raw.get("origin") or "seed_only")
        if resolved.get("parse_status") == "resolved":
            evidence_class = "external_provider"
        elif origin == "repo_local_extracted":
            evidence_class = "repo_local_extracted"
        else:
            evidence_class = "parsed_locator"
        record = {
            "source_type": resolved.get("source_type") or raw.get("kind") or "web",
            "provider_type": resolved.get("provider_type") or "seed",
            "provider_identifier": locator_info.get("identifier") or resolved.get("normalized_id") or "",
            "provider_locator": locator_info.get("raw_locator") or "",
            "locator_type": resolved.get("locator_type") or locator_info.get("locator_type") or "seed",
            "raw_locator": locator_info.get("raw_locator") or "",
            "normalized_id": resolved.get("normalized_id") or locator_info.get("normalized_id") or "",
            "title": resolved.get("title") or raw.get("title") or "",
            "summary": resolved.get("summary") or raw.get("summary") or "",
            "query": str(raw.get("query") or raw.get("title") or ""),
            "url": resolved.get("url") or locator_info.get("url") or raw.get("source_url") or "",
            "authors": resolved.get("authors") or [],
            "year": resolved.get("year"),
            "venue": resolved.get("venue") or "",
            "repo_full_name": resolved.get("repo_full_name") or raw.get("source_repo") or "",
            "doi": resolved.get("doi") or "",
            "arxiv_id": resolved.get("arxiv_id") or "",
            "evidence_class": evidence_class,
            "parse_status": resolved.get("parse_status") or "parsed-only",
            "fetch_status": resolved.get("fetch_status") or "parsed-only",
            "provider_metadata": resolved.get("provider_metadata") or {},
            "source_repo": raw.get("source_repo") or resolved.get("repo_full_name") or "",
            "source_file": raw.get("source_file") or resolved.get("source_file") or locator_info.get("source_file") or "",
            "source_symbol": raw.get("source_symbol") or "",
            "origins": [origin],
            "extracted_from_repo_paths": list(raw.get("extracted_from_repo_paths") or []),
            "selection_hints": [str(raw.get("query") or ""), str(raw.get("title") or "")],
        }
        return normalize_record(record)

    return normalize_record(
        {
            "source_type": raw.get("kind") or "query",
            "provider_type": "seed",
            "provider_identifier": str(raw.get("query") or raw.get("title") or ""),
            "provider_locator": str(raw.get("source_url") or ""),
            "locator_type": "seed",
            "raw_locator": str(raw.get("source_url") or raw.get("query") or raw.get("title") or ""),
            "normalized_id": "",
            "title": str(raw.get("title") or raw.get("query") or "seed-source"),
            "summary": str(raw.get("summary") or ""),
            "query": str(raw.get("query") or raw.get("title") or ""),
            "url": str(raw.get("source_url") or ""),
            "repo_full_name": str(raw.get("source_repo") or ""),
            "evidence_class": "repo_local_extracted" if str(raw.get("origin") or "") == "repo_local_extracted" else "seed_only",
            "parse_status": "seed-only",
            "fetch_status": "seed-only",
            "source_repo": str(raw.get("source_repo") or ""),
            "source_file": str(raw.get("source_file") or ""),
            "source_symbol": str(raw.get("source_symbol") or ""),
            "origins": [str(raw.get("origin") or "seed_only")],
            "extracted_from_repo_paths": list(raw.get("extracted_from_repo_paths") or []),
            "selection_hints": [str(raw.get("query") or ""), str(raw.get("title") or "")],
        }
    )


def run_lookup_pass(
    *,
    sources_dir: Path,
    repo_path: Path,
    analysis_output_dir: Optional[Path],
    campaign: Dict[str, Any],
    analysis_data: Dict[str, Any],
    code_plan: Dict[str, Any],
) -> Dict[str, Any]:
    sources_dir.mkdir(parents=True, exist_ok=True)
    output_dir = analysis_output_dir or (sources_dir.parent / "analysis_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    lookup_config = campaign.get("research_lookup", {}) if isinstance(campaign.get("research_lookup"), dict) else {}
    seed_records = collect_seed_records(campaign, analysis_data, code_plan)
    repo_local_seeds = extract_repo_local_seeds(repo_path) if lookup_config.get("enable_repo_local_extraction", True) else []
    raw_records = dedupe_preserving_order([*seed_records, *repo_local_seeds])
    resolved_records = [resolve_provider_record(raw, lookup_config) for raw in raw_records]
    stored_bundle = store_records(sources_dir, resolved_records)
    records = stored_bundle["records"]
    cache_stats = {
        "cache_hits": stored_bundle.get("cache_hits", 0),
        "cache_misses": stored_bundle.get("cache_misses", 0),
        "merge_upgrades": stored_bundle.get("merge_upgrades", 0),
    }
    summary_path = write_sources_summary(sources_dir, records)
    inventory_path = write_source_inventory(
        output_dir,
        records=records,
        repo_local_extractions=repo_local_seeds,
        cache_stats=cache_stats,
    )
    support_bundle = build_source_support(campaign, records, repo_local_seeds, cache_stats)
    support_path = write_source_support(output_dir, support_bundle)
    records_by_evidence_class = sorted({str(item.get("evidence_class") or "") for item in records if item.get("evidence_class")})
    return {
        "schema_version": "2.0",
        "mode": "free-first-cache-first",
        "sources_dir": str(sources_dir),
        "records_dir": stored_bundle.get("records_dir"),
        "index_path": stored_bundle.get("index_path"),
        "summary_path": str(summary_path),
        "inventory_path": str(inventory_path),
        "support_path": str(support_path),
        "support_bundle": support_bundle,
        "records": records,
        "records_by_kind": sorted({str(item.get("source_type") or "") for item in records if item.get("source_type")}),
        "records_by_provider": sorted({str(item.get("provider_type") or "") for item in records if item.get("provider_type")}),
        "records_by_evidence_class": records_by_evidence_class,
        "cache_hits": stored_bundle.get("cache_hits", 0),
        "cache_misses": stored_bundle.get("cache_misses", 0),
        "repo_extracted_locators": [item.get("raw_locator") for item in repo_local_seeds],
        "repo_local_extractions": repo_local_seeds,
        "queries": [item.get("query") for item in raw_records if item.get("kind") == "query"],
        "optional_provider_used": False,
    }
