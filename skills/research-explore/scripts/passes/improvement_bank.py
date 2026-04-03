"""Improvement mining pass for research-explore."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Sequence

from lookup.record_schema import normalize_evidence_class


def tokenize(value: str) -> List[str]:
    return [token for token in re.split(r"[^a-z0-9]+", str(value).lower()) if len(token) > 2]


def clamp(value: Any, default: float = 0.5) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = default
    return max(0.0, min(1.0, numeric))


def record_evidence_class(record: Dict[str, Any]) -> str:
    if record.get("evidence_class"):
        return normalize_evidence_class(record.get("evidence_class"))
    return "seed_only" if str(record.get("provider_type") or "seed") == "seed" else "external_provider"


def record_evidence_weight(record: Dict[str, Any]) -> float:
    if record.get("evidence_weight") is not None:
        return clamp(record.get("evidence_weight"), default=0.2)
    evidence = record_evidence_class(record)
    if evidence == "external_provider":
        return 1.0
    if evidence == "parsed_locator":
        return 0.65
    if evidence == "repo_local_extracted":
        return 0.45
    return 0.2


def baseline_distance_score(baseline_gate: Dict[str, Any]) -> float:
    gap = baseline_gate.get("gap_to_sota")
    relative = baseline_gate.get("relative_gap_to_sota")
    if gap is not None:
        return clamp(float(gap) / 5.0, default=0.0)
    if relative is not None:
        return clamp(float(relative) / 0.10, default=0.0)
    return 0.0


def match_sources(idea: Dict[str, Any], source_records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tokens = set(
        tokenize(idea.get("summary"))
        + tokenize(idea.get("target_component"))
        + tokenize(idea.get("change_scope"))
    )
    matches: List[tuple[int, Dict[str, Any]]] = []
    for record in source_records:
        haystack = " ".join(
            [
                str(record.get("title") or ""),
                str(record.get("summary") or ""),
                str(record.get("query") or ""),
            ]
        ).lower()
        score = sum(1 for token in tokens if token in haystack)
        if score > 0:
            matches.append((score, record_evidence_weight(record), record))
    matches.sort(key=lambda item: (-item[0], -item[1], item[2].get("source_id", "")))
    return [record for _, _weight, record in matches[:4]]


def matched_sources_for_idea(idea: Dict[str, Any], lookup_bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
    source_records = lookup_bundle.get("records", [])
    support_bundle = lookup_bundle.get("support_bundle", {})
    support_index = support_bundle.get("support_index_by_candidate_idea", {})
    idea_support = support_index.get(str(idea.get("id") or ""), {})
    matched_ids = idea_support.get("matched_source_ids", [])
    lookup = {item.get("source_id"): item for item in source_records if item.get("source_id")}
    matched = [lookup[source_id] for source_id in matched_ids if source_id in lookup]
    return matched or match_sources(idea, source_records)


def interface_fit_seed(
    idea: Dict[str, Any],
    analysis_data: Dict[str, Any],
    code_plan: Dict[str, Any],
) -> float:
    tokens = set(tokenize(idea.get("target_component")) + tokenize(idea.get("summary")))
    # Sparse repos should start from a neutral fit rather than failing the idea gate by default.
    score = 0.50
    candidate_targets = code_plan.get("candidate_edit_targets", [])
    if any(any(token in path.lower() for token in tokens) for path in candidate_targets):
        score += 0.25
    symbol_hints = analysis_data.get("symbol_hints", [])
    if any(any(token in str(item).lower() for token in tokens) for item in symbol_hints):
        score += 0.20
    module_files = analysis_data.get("module_files", [])
    if any(any(token in path.lower() for token in tokens) for path in module_files):
        score += 0.15
    if analysis_data.get("constructor_candidates"):
        score += 0.05
    if analysis_data.get("forward_candidates"):
        score += 0.05
    return clamp(score, default=0.5)


def patch_surface_score(code_plan: Dict[str, Any], idea: Dict[str, Any]) -> float:
    target_count = len(code_plan.get("candidate_edit_targets", []))
    support_count = len(idea.get("supporting_changes", []) or [])
    return clamp(0.15 + 0.08 * target_count + 0.05 * support_count, default=0.4)


def dependency_drag_score(idea: Dict[str, Any], matched_sources: Sequence[Dict[str, Any]]) -> float:
    return clamp(
        0.10
        + 0.08 * len(idea.get("supporting_changes", []) or [])
        + 0.04 * max(0, len(matched_sources) - 1),
        default=0.2,
    )


def innovation_story_strength(idea: Dict[str, Any], matched_sources: Sequence[Dict[str, Any]]) -> float:
    novelty_terms = {"novel", "cross", "adapter", "transplant", "hybrid", "augment", "improve", "replace"}
    summary_tokens = set(tokenize(idea.get("summary")))
    base = 0.35 + 0.10 * len(matched_sources)
    if novelty_terms & summary_tokens:
        base += 0.15
    if idea.get("target_component"):
        base += 0.10
    return clamp(base, default=0.5)


def source_support_strength(matched_sources: Sequence[Dict[str, Any]]) -> float:
    external_weight = sum(
        record_evidence_weight(item)
        for item in matched_sources
        if record_evidence_class(item) == "external_provider"
    )
    parsed_weight = sum(
        record_evidence_weight(item)
        for item in matched_sources
        if record_evidence_class(item) == "parsed_locator"
    )
    repo_local_weight = sum(
        record_evidence_weight(item)
        for item in matched_sources
        if record_evidence_class(item) == "repo_local_extracted"
    )
    seed_weight = sum(
        record_evidence_weight(item)
        for item in matched_sources
        if record_evidence_class(item) == "seed_only"
    )
    return clamp(
        0.08
        + 0.28 * min(external_weight, 2.0)
        + 0.12 * min(parsed_weight, 2.0)
        + 0.08 * min(repo_local_weight, 2.0)
        + 0.04 * min(seed_weight, 2.0),
        default=0.25,
    )


def build_rationale(idea: Dict[str, Any], baseline_gate: Dict[str, Any], matched_sources: Sequence[Dict[str, Any]]) -> str:
    source_ids = ", ".join(item["source_id"] for item in matched_sources[:3]) or "no-source-id"
    external_ids = ", ".join(
        item["source_id"]
        for item in matched_sources
        if record_evidence_class(item) == "external_provider"
    ) or "no-external-source-id"
    if baseline_gate.get("decision") == "proceed":
        return (
            f"Baseline gate permits follow-up work; candidate stays within the frozen evaluation contract and is "
            f"supported by external source references {external_ids} and bounded lookup references {source_ids}."
        )
    if baseline_gate.get("decision") == "borderline":
        return (
            f"Baseline is borderline; keep the patch surface tight and rely on source references {source_ids} "
            f"before widening execution."
        )
    return f"Use source references {source_ids} to keep the candidate auditable and bounded."


def build_validation_path(campaign: Dict[str, Any], idea: Dict[str, Any]) -> str:
    evaluation_source = campaign.get("evaluation_source", {})
    command = str(evaluation_source.get("command") or "frozen-eval-command")
    return f"Preserve `{command}` and verify `{idea.get('change_scope') or 'candidate change'}` via short-run gate before any wider run."


def build_improvement_bank(
    campaign: Dict[str, Any],
    analysis_data: Dict[str, Any],
    code_plan: Dict[str, Any],
    lookup_bundle: Dict[str, Any],
    baseline_gate: Dict[str, Any],
) -> List[Dict[str, Any]]:
    bank: List[Dict[str, Any]] = []
    baseline_distance = baseline_distance_score(baseline_gate)
    for idea in campaign.get("candidate_ideas", []):
        matched_sources = matched_sources_for_idea(idea, lookup_bundle)
        external_source_reference = [
            item["source_id"]
            for item in matched_sources
            if record_evidence_class(item) == "external_provider"
        ]
        parsed_locator_reference = [
            item["source_id"]
            for item in matched_sources
            if record_evidence_class(item) == "parsed_locator"
        ]
        repo_local_source_reference = [
            item["source_id"]
            for item in matched_sources
            if record_evidence_class(item) == "repo_local_extracted"
        ]
        source_evidence_summary = {
            "external_provider_records": len(external_source_reference),
            "parsed_locator_records": len(parsed_locator_reference),
            "repo_local_extracted_records": len(repo_local_source_reference),
            "seed_only_records": sum(1 for item in matched_sources if record_evidence_class(item) == "seed_only"),
            "weighted_external_support": round(
                sum(record_evidence_weight(item) for item in matched_sources if record_evidence_class(item) == "external_provider"),
                4,
            ),
            "weighted_parsed_locator_support": round(
                sum(record_evidence_weight(item) for item in matched_sources if record_evidence_class(item) == "parsed_locator"),
                4,
            ),
            "weighted_repo_local_support": round(
                sum(record_evidence_weight(item) for item in matched_sources if record_evidence_class(item) == "repo_local_extracted"),
                4,
            ),
            "weighted_seed_support": round(
                sum(record_evidence_weight(item) for item in matched_sources if record_evidence_class(item) == "seed_only"),
                4,
            ),
        }
        patch_surface = patch_surface_score(code_plan, idea)
        record = {
            "id": str(idea.get("id") or "idea"),
            "summary": str(idea.get("summary") or "Candidate improvement"),
            "rationale": build_rationale(idea, baseline_gate, matched_sources),
            "target_component": str(idea.get("target_component") or "unspecified"),
            "source_reference": [item["source_id"] for item in matched_sources],
            "external_source_reference": external_source_reference,
            "parsed_locator_reference": parsed_locator_reference,
            "repo_local_source_reference": repo_local_source_reference,
            "source_evidence_summary": source_evidence_summary,
            "expected_upside": clamp(idea.get("expected_upside"), default=0.5),
            "single_variable_fit": clamp(idea.get("single_variable_fit"), default=0.8),
            "implementation_risk": clamp(idea.get("implementation_risk"), default=0.5),
            "eval_risk": clamp(idea.get("eval_risk"), default=0.5),
            "rollback_ease": clamp(idea.get("rollback_ease"), default=0.5),
            "patch_surface": patch_surface,
            "dependency_drag": dependency_drag_score(idea, matched_sources),
            "interface_fit": interface_fit_seed(idea, analysis_data, code_plan),
            "execution_cost": clamp(idea.get("estimated_runtime_cost"), default=0.5),
            "innovation_story_strength": innovation_story_strength(idea, matched_sources),
            "source_support_strength": source_support_strength(matched_sources),
            "baseline_distance": baseline_distance,
            "validation_path": build_validation_path(campaign, idea),
            "innovation_note": (
                f"Candidate-only story for `{idea.get('change_scope') or 'change'}`; do not present as verified novelty."
            ),
            "provenance": {
                "campaign_idea_id": str(idea.get("id") or "idea"),
                "matched_source_ids": [item["source_id"] for item in matched_sources],
                "matched_external_source_ids": external_source_reference,
                "analysis_files": analysis_data.get("module_files", [])[:4],
            },
        }
        bank.append(record)
    return bank


def write_improvement_bank(output_dir: Path, bank: Sequence[Dict[str, Any]]) -> Path:
    lines = [
        "# Improvement Bank",
        "",
        "Structured candidate improvements for the third research scenario.",
        "",
    ]
    if not bank:
        lines.append("- None.")
    else:
        for item in bank:
            lines.extend(
                [
                    f"## {item['id']}",
                    "",
                    f"- Summary: {item['summary']}",
                    f"- Target component: `{item['target_component']}`",
                    f"- Source references: {', '.join(item['source_reference']) or 'none'}",
                    f"- External source references: {', '.join(item.get('external_source_reference', [])) or 'none'}",
                    f"- Parsed locator references: {', '.join(item.get('parsed_locator_reference', [])) or 'none'}",
                    f"- Repo-local source references: {', '.join(item.get('repo_local_source_reference', [])) or 'none'}",
                    f"- Evidence summary: external={item.get('source_evidence_summary', {}).get('external_provider_records', 0)} parsed={item.get('source_evidence_summary', {}).get('parsed_locator_records', 0)} repo_local={item.get('source_evidence_summary', {}).get('repo_local_extracted_records', 0)} seed={item.get('source_evidence_summary', {}).get('seed_only_records', 0)}",
                    f"- Single-variable fit: `{item['single_variable_fit']}`",
                    f"- Interface fit: `{item['interface_fit']}`",
                    f"- Patch surface: `{item['patch_surface']}`",
                    f"- Dependency drag: `{item['dependency_drag']}`",
                    f"- Validation path: {item['validation_path']}",
                    f"- Rationale: {item['rationale']}",
                    "",
                ]
            )
    path = output_dir / "IMPROVEMENT_BANK.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_improvement_bank_pass(
    *,
    analysis_output_dir: Path,
    campaign: Dict[str, Any],
    analysis_data: Dict[str, Any],
    code_plan: Dict[str, Any],
    lookup_bundle: Dict[str, Any],
    baseline_gate: Dict[str, Any],
) -> Dict[str, Any]:
    bank = build_improvement_bank(campaign, analysis_data, code_plan, lookup_bundle, baseline_gate)
    path = write_improvement_bank(analysis_output_dir, bank)
    return {
        "schema_version": "1.0",
        "artifact_path": str(path),
        "items": bank,
    }
