"""Atomic academic concept decomposition for ai-research-explore."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Sequence


BLOCKED_SCOPES = {"unspecified", "broad_rewrite", "rewrite-everything"}


def tokenize(value: Any) -> List[str]:
    return [token for token in re.split(r"[^a-z0-9]+", str(value or "").lower()) if len(token) > 2]


def unique_preserving(values: Sequence[str], *, limit: int | None = None) -> List[str]:
    ordered: List[str] = []
    for value in values:
        if not value or value in ordered:
            continue
        ordered.append(value)
        if limit is not None and len(ordered) >= limit:
            break
    return ordered


def humanize_slug(value: str) -> str:
    text = str(value or "").replace("_", " ").replace("-", " ").strip()
    return " ".join(part.capitalize() for part in text.split()) or "Atomic Concept"


def classify_surface(path: str) -> str:
    lowered = str(path).lower()
    if any(token in lowered for token in ("config", ".yaml", ".yml", ".json", ".toml", ".ini")):
        return "config"
    if any(token in lowered for token in ("data", "dataset", "loader", "transform")):
        return "data interface"
    if any(token in lowered for token in ("eval", "metric", "benchmark", "validation", "test")):
        return "evaluation adapter"
    if any(token in lowered for token in ("train", "trainer", "loss", "optim", "schedule")):
        return "training"
    return "model"


def formula_support(selected_idea: Dict[str, Any], lookup_bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
    source_ids = list(selected_idea.get("source_reference", []) or [])
    records = {item.get("source_id"): item for item in lookup_bundle.get("records", []) if item.get("source_id")}
    support: List[Dict[str, Any]] = []
    for source_id in source_ids[:3]:
        record = records.get(source_id) or {}
        support.append(
            {
                "source_id": source_id,
                "title": record.get("title") or "Unresolved source reference",
                "evidence_class": record.get("evidence_class") or "unresolved",
                "note": "Use this source only as bounded academic support; it is not a novelty proof.",
            }
        )
    if not support:
        support.append(
            {
                "source_id": "none",
                "title": "No directly matched formula-level source",
                "evidence_class": "none",
                "note": "Concept remains grounded in repo-local constraints rather than directly verified source material.",
            }
        )
    return support


def code_support(selected_idea: Dict[str, Any], source_mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
    selected_source = source_mapping.get("selected_source_record", {}) or {}
    target_location_map = source_mapping.get("target_location_map", []) or []
    support: List[Dict[str, Any]] = []
    if selected_source:
        support.append(
            {
                "source_id": selected_source.get("source_id") or "selected-source-record",
                "source_repo": selected_source.get("source_repo") or "",
                "source_file": selected_source.get("source_file") or "",
                "source_symbol": selected_source.get("source_symbol") or "",
                "note": "Candidate source triple for a bounded transplant or adaptation path.",
            }
        )
    if target_location_map:
        support.append(
            {
                "source_id": "repo-local-target-map",
                "source_repo": "current-research",
                "source_file": target_location_map[0].get("file") or "",
                "source_symbol": target_location_map[0].get("target_symbol") or "",
                "note": "Repo-local implementation target inferred from source mapping.",
            }
        )
    if not support:
        support.append(
            {
                "source_id": "none",
                "source_repo": "current-research",
                "source_file": "",
                "source_symbol": "",
                "note": "No concrete code support could be resolved.",
            }
        )
    return support


def unit_validation_strategy(surface: str, selected_idea: Dict[str, Any], variant_spec: Dict[str, Any]) -> str:
    if surface == "config":
        return f"Verify that `{selected_idea.get('change_scope', 'candidate change')}` can be isolated through config or CLI overrides without touching the frozen eval contract."
    if surface == "evaluation adapter":
        return "Keep evaluation surfaces protected; validate only compatibility and do not change metric semantics."
    if variant_spec.get("base_command"):
        return f"Smoke the implementation through `{variant_spec['base_command']}` with a short-run gate before any broader candidate run."
    return "Use a bounded static and short-run validation path before claiming the idea is implementable."


def implementation_risk(selected_idea: Dict[str, Any], surface: str) -> float:
    base = float(selected_idea.get("implementation_risk") or 0.4)
    if surface in {"training", "evaluation adapter"}:
        base += 0.10
    return max(0.0, min(1.0, round(base, 4)))


def scientific_meaning_risk(selected_idea: Dict[str, Any], surface: str) -> float:
    base = float(selected_idea.get("eval_risk") or 0.3)
    if surface == "evaluation adapter":
        base += 0.20
    if surface == "training":
        base += 0.10
    return max(0.0, min(1.0, round(base, 4)))


def build_atomic_units(
    *,
    selected_idea: Dict[str, Any],
    analysis_data: Dict[str, Any],
    source_mapping: Dict[str, Any],
    lookup_bundle: Dict[str, Any],
    variant_spec: Dict[str, Any],
) -> tuple[List[Dict[str, Any]], List[str]]:
    blockers: List[str] = []
    change_scope = str(selected_idea.get("change_scope") or "unspecified")
    target_component = str(selected_idea.get("target_component") or "unspecified")
    if change_scope in BLOCKED_SCOPES:
        blockers.append("selected-idea-change-scope-too-broad-for-atomic-decomposition")
    target_location_map = source_mapping.get("target_location_map", []) or []
    module_candidates = source_mapping.get("module_candidates", []) or []
    if not target_location_map and not module_candidates:
        blockers.append("no-target-surface-for-atomic-decomposition")

    code_files = unique_preserving(
        [
            str(item.get("file") or "")
            for item in target_location_map
            if str(item.get("role") or "") == "code"
        ]
        + [str(item.get("target_file") or "") for item in module_candidates],
        limit=5,
    )
    config_files = unique_preserving(
        [
            str(item.get("file") or "")
            for item in target_location_map
            if str(item.get("role") or "") == "config"
        ]
        + list(analysis_data.get("config_binding_hints", [])),
        limit=4,
    )
    code_symbols = unique_preserving(
        [str(item.get("target_symbol") or "") for item in target_location_map if item.get("target_symbol")]
        + list(analysis_data.get("constructor_candidates", []))
        + list(analysis_data.get("forward_candidates", [])),
        limit=6,
    )

    units: List[Dict[str, Any]] = []
    if code_files:
        surface = classify_surface(code_files[0])
        units.append(
            {
                "atomic_id": f"{selected_idea.get('id', 'idea')}-atomic-01",
                "concept_name": humanize_slug(change_scope or target_component),
                "concept_summary": str(selected_idea.get("summary") or "Bounded implementation concept"),
                "why_needed": f"Translate the selected idea into repo-local `{surface}` logic without broad architectural rewrites.",
                "formula_support": formula_support(selected_idea, lookup_bundle),
                "code_support": code_support(selected_idea, source_mapping),
                "expected_code_surface": surface,
                "target_file_candidates": code_files,
                "target_symbol_candidates": code_symbols or unique_preserving([target_component], limit=3),
                "validation_strategy": unit_validation_strategy(surface, selected_idea, variant_spec),
                "implementation_risk": implementation_risk(selected_idea, surface),
                "scientific_meaning_risk": scientific_meaning_risk(selected_idea, surface),
            }
        )
    if config_files:
        units.append(
            {
                "atomic_id": f"{selected_idea.get('id', 'idea')}-atomic-02",
                "concept_name": f"{humanize_slug(change_scope)} Control Surface",
                "concept_summary": f"Expose `{change_scope}` as a single-variable ablation surface rather than an entangled rewrite.",
                "why_needed": "Keep attribution clear, rollback easy, and short-run feasibility auditable.",
                "formula_support": formula_support(selected_idea, lookup_bundle),
                "code_support": code_support(selected_idea, source_mapping),
                "expected_code_surface": "config",
                "target_file_candidates": config_files,
                "target_symbol_candidates": unique_preserving(
                    list(analysis_data.get("config_binding_hints", [])) + [change_scope, target_component],
                    limit=6,
                ),
                "validation_strategy": unit_validation_strategy("config", selected_idea, variant_spec),
                "implementation_risk": implementation_risk(selected_idea, "config"),
                "scientific_meaning_risk": scientific_meaning_risk(selected_idea, "config"),
            }
        )

    if not units:
        blockers.append("selected-idea-could-not-be-split-into-implementable-atomic-units")
    return units, unique_preserving(blockers)


def write_atomic_markdown(output_dir: Path, payload: Dict[str, Any]) -> Path:
    lines = [
        "# Atomic Idea Map",
        "",
        f"- Status: `{payload.get('status', 'blocked')}`",
        f"- Selected idea: `{payload.get('selected_idea_id', 'none')}`",
        "",
        "## Blockers",
        "",
    ]
    blockers = payload.get("blockers", [])
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- None.")
    lines.extend(["", "## Atomic Units", ""])
    atomic_units = payload.get("atomic_units", [])
    if not atomic_units:
        lines.append("- None.")
    else:
        for unit in atomic_units:
            lines.extend(
                [
                    f"### {unit['atomic_id']} - {unit['concept_name']}",
                    "",
                    f"- Summary: {unit['concept_summary']}",
                    f"- Why needed: {unit['why_needed']}",
                    f"- Expected code surface: `{unit['expected_code_surface']}`",
                    f"- Target file candidates: {', '.join(unit.get('target_file_candidates', [])) or 'none'}",
                    f"- Target symbol candidates: {', '.join(unit.get('target_symbol_candidates', [])) or 'none'}",
                    f"- Validation strategy: {unit['validation_strategy']}",
                    f"- Implementation risk: `{unit['implementation_risk']}`",
                    f"- Scientific meaning risk: `{unit['scientific_meaning_risk']}`",
                    "",
                ]
            )
    path = output_dir / "ATOMIC_IDEA_MAP.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_atomic_idea_decomposition_pass(
    *,
    analysis_output_dir: Path,
    selected_idea: Dict[str, Any],
    analysis_data: Dict[str, Any],
    source_mapping: Dict[str, Any],
    lookup_bundle: Dict[str, Any],
    current_research: str,
    variant_spec: Dict[str, Any],
) -> Dict[str, Any]:
    del current_research
    atomic_units, blockers = build_atomic_units(
        selected_idea=selected_idea,
        analysis_data=analysis_data,
        source_mapping=source_mapping,
        lookup_bundle=lookup_bundle,
        variant_spec=variant_spec,
    )
    payload = {
        "schema_version": "1.0",
        "status": "blocked" if blockers else "ready",
        "selected_idea_id": str(selected_idea.get("id") or ""),
        "atomic_units": atomic_units,
        "atomic_unit_count": len(atomic_units),
        "blockers": blockers,
    }
    json_path = analysis_output_dir / "ATOMIC_IDEA_MAP.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    markdown_path = write_atomic_markdown(analysis_output_dir, payload)
    return {
        **payload,
        "artifact_paths": [str(markdown_path), str(json_path)],
        "artifact_path": str(json_path),
    }

