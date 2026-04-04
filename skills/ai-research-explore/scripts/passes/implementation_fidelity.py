"""Implementation fidelity checks for ai-research-explore."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple


VERIFICATION_MODE_BY_LEVEL = {
    "not_checked": "not_checked",
    "planned_only": "not_checked",
    "heuristic_only": "heuristic",
    "executor_observed": "observed",
    "diff_verified": "observed",
}


def unique_preserving(values: Sequence[str]) -> List[str]:
    ordered: List[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in ordered:
            continue
        ordered.append(text)
    return ordered


def prefixed_site_entries(values: Sequence[str], *, label: str, source: str) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        entries.append(
            {
                "site": f"{label}:{text}",
                "path": text,
                "source": source,
            }
        )
    return entries


def expected_files_for_unit(unit: Dict[str, Any]) -> List[str]:
    return unique_preserving(str(item) for item in unit.get("target_file_candidates", []))


def path_matches_expected(path: str, expected_files: Sequence[str]) -> bool:
    normalized_path = str(path or "").strip().lower()
    expected_lookup = {str(item or "").strip().lower() for item in expected_files if str(item or "").strip()}
    return bool(normalized_path and normalized_path in expected_lookup)


def filter_path_entries(entries: Sequence[Dict[str, str]], expected_files: Sequence[str]) -> List[Dict[str, str]]:
    return [entry for entry in entries if path_matches_expected(entry.get("path", ""), expected_files)]


def collect_run_path_entries(executed_runs: Sequence[Dict[str, Any]]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    diff_entries: List[Dict[str, str]] = []
    touched_entries: List[Dict[str, str]] = []
    for item in executed_runs:
        run_id = str(item.get("id") or "executed-run")
        diff_entries.extend(
            prefixed_site_entries(
                item.get("changed_files", []) or [],
                label="executor-changed-file",
                source=f"executed_runs[{run_id}].changed_files",
            )
        )
        diff_entries.extend(
            prefixed_site_entries(
                item.get("new_files", []) or [],
                label="executor-new-file",
                source=f"executed_runs[{run_id}].new_files",
            )
        )
        diff_entries.extend(
            prefixed_site_entries(
                item.get("deleted_files", []) or [],
                label="executor-deleted-file",
                source=f"executed_runs[{run_id}].deleted_files",
            )
        )
        touched_entries.extend(
            prefixed_site_entries(
                item.get("touched_paths", []) or [],
                label="executor-touched-path",
                source=f"executed_runs[{run_id}].touched_paths",
            )
        )
    return diff_entries, touched_entries


def planned_site_entries(
    unit: Dict[str, Any],
    *,
    source_mapping: Dict[str, Any],
    code_plan: Dict[str, Any],
) -> List[Dict[str, str]]:
    expected_files = expected_files_for_unit(unit)
    entries = prefixed_site_entries(
        expected_files,
        label="expected-target-file",
        source="atomic_bundle.target_file_candidates",
    )
    entries.extend(
        filter_path_entries(
            prefixed_site_entries(
                code_plan.get("candidate_edit_targets", []) or [],
                label="code-plan-target",
                source="code_plan.candidate_edit_targets",
            ),
            expected_files,
        )
    )
    entries.extend(
        filter_path_entries(
            prefixed_site_entries(
                [
                    item.get("file")
                    for item in source_mapping.get("target_location_map", []) or []
                    if str(item.get("file") or "").strip()
                ],
                label="source-mapping-target",
                source="source_mapping.target_location_map",
            ),
            expected_files,
        )
    )
    entries.extend(
        filter_path_entries(
            prefixed_site_entries(
                [
                    target
                    for item in source_mapping.get("minimal_patch_plan", []) or []
                    for target in (item.get("target_files", []) or [])
                    if str(target or "").strip()
                ],
                label="minimal-patch-target",
                source="source_mapping.minimal_patch_plan",
            ),
            expected_files,
        )
    )
    deduped: List[Dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for entry in entries:
        marker = (entry["site"], entry["source"])
        if marker in seen:
            continue
        deduped.append(entry)
        seen.add(marker)
    return deduped


def heuristic_site_entries(
    unit: Dict[str, Any],
    *,
    selected_idea: Dict[str, Any],
    experiment_manifest: Dict[str, Any],
    executed_runs: Sequence[Dict[str, Any]],
) -> List[Dict[str, str]]:
    change_scope = str(selected_idea.get("change_scope") or "").strip()
    surface = str(unit.get("expected_code_surface") or "")
    entries: List[Dict[str, str]] = []
    if surface == "config" and change_scope:
        config_overrides = experiment_manifest.get("config_overrides", {}) or {}
        if change_scope in config_overrides:
            entries.append(
                {
                    "site": f"config-override:{change_scope}",
                    "path": "",
                    "source": "experiment_manifest.config_overrides",
                }
            )
    if surface == "config" and change_scope:
        for item in executed_runs:
            run_id = str(item.get("id") or "executed-run")
            axes = item.get("axes", {}) or {}
            if change_scope in axes:
                entries.append(
                    {
                        "site": f"executed-axis:{change_scope}",
                        "path": "",
                        "source": f"executed_runs[{run_id}].axes",
                    }
                )
    deduped: List[Dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for entry in entries:
        marker = (entry["site"], entry["source"])
        if marker in seen:
            continue
        deduped.append(entry)
        seen.add(marker)
    return deduped


def observed_site_entries(unit: Dict[str, Any], executed_runs: Sequence[Dict[str, Any]]) -> Tuple[List[Dict[str, str]], str]:
    expected_files = expected_files_for_unit(unit)
    diff_entries, touched_entries = collect_run_path_entries(executed_runs)
    matched_diff_entries = filter_path_entries(diff_entries, expected_files)
    if matched_diff_entries:
        return matched_diff_entries, "diff_verified"
    matched_touched_entries = filter_path_entries(touched_entries, expected_files)
    if matched_touched_entries:
        return matched_touched_entries, "executor_observed"
    return [], "not_checked"


def common_failure_mode(unit: Dict[str, Any]) -> str:
    surface = str(unit.get("expected_code_surface") or "model")
    if surface == "config":
        return "runtime override exists but no repo-local config/code diff was verified"
    if surface == "evaluation adapter":
        return "metric surface drifted instead of preserving the frozen eval contract"
    if surface == "training":
        return "training hook changed without a bounded single-variable story"
    return "target module was planned, but no repo-local implementation diff was verified"


def unit_state(
    *,
    phase: str,
    surface: str,
    planned_entries: Sequence[Dict[str, str]],
    heuristic_entries: Sequence[Dict[str, str]],
    observed_entries: Sequence[Dict[str, str]],
    observed_level: str,
    executed_runs: Sequence[Dict[str, Any]],
) -> Tuple[str, str, str]:
    if observed_entries:
        if observed_level == "diff_verified":
            return (
                "likely-implemented",
                "diff_verified",
                "Observed matching repo-local diff evidence for this atomic unit.",
            )
        return (
            "partial",
            "executor_observed",
            "Observed executor-emitted touched-path evidence for this atomic unit, but the change type stayed coarser than a diff-verified file class.",
        )

    if heuristic_entries:
        if surface == "config":
            return (
                "partial",
                "heuristic_only",
                "Runtime overrides or executed axes lined up with the planned config surface, but no repo-local diff was verified.",
            )
        return (
            "unclear",
            "heuristic_only",
            "Heuristic execution signals existed, but no repo-local implementation diff was verified.",
        )

    if phase == "pre-execution":
        if planned_entries:
            return (
                "not-started",
                "planned_only",
                "Only implementation expectations are available at pre-execution time.",
            )
        return (
            "not-started",
            "not_checked",
            "No implementation evidence has been checked yet.",
        )

    if executed_runs:
        if planned_entries:
            return (
                "unclear",
                "planned_only",
                "Execution completed, but no observed implementation evidence matched the planned sites.",
            )
        return (
            "unclear",
            "not_checked",
            "Execution completed, but no implementation evidence matched this atomic unit.",
        )

    if planned_entries:
        return (
            "not-started",
            "planned_only",
            "Only implementation expectations are available; no executor evidence exists yet.",
        )
    return (
        "not-started",
        "not_checked",
        "No implementation evidence was available.",
    )


def summarize_fidelity(units: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    states: Dict[str, int] = {}
    verification_levels: Dict[str, int] = {}
    verification_modes: Dict[str, int] = {}
    for unit in units:
        state = str(unit.get("fidelity_state") or "unknown")
        states[state] = states.get(state, 0) + 1
        level = str(unit.get("verification_level") or "unknown")
        verification_levels[level] = verification_levels.get(level, 0) + 1
        mode = str(unit.get("verification_mode") or "unknown")
        verification_modes[mode] = verification_modes.get(mode, 0) + 1
    return {
        "unit_count": len(units),
        "states": states,
        "verification_levels": verification_levels,
        "verification_modes": verification_modes,
    }


def site_values(entries: Sequence[Dict[str, str]]) -> List[str]:
    return unique_preserving(entry.get("site", "") for entry in entries)


def write_fidelity_markdown(output_dir: Path, payload: Dict[str, Any]) -> Path:
    lines = [
        "# Implementation Fidelity",
        "",
        f"- Status: `{payload.get('status', 'ready')}`",
        f"- Phase: `{payload.get('phase', 'pre-execution')}`",
        f"- Selected idea: `{payload.get('selected_idea_id', 'none')}`",
        "",
        "## Summary",
        "",
        f"- Atomic unit count: `{payload.get('fidelity_summary', {}).get('unit_count', 0)}`",
        f"- States: `{payload.get('fidelity_summary', {}).get('states', {})}`",
        f"- Verification levels: `{payload.get('fidelity_summary', {}).get('verification_levels', {})}`",
        "",
        "## Units",
        "",
    ]
    fidelity_units = payload.get("fidelity_units", [])
    if not fidelity_units:
        lines.append("- None.")
    else:
        for unit in fidelity_units:
            lines.extend(
                [
                    f"### {unit['atomic_id']}",
                    "",
                    f"- Expected implementation site: surface=`{unit['expected_implementation_site']['surface']}` files={', '.join(unit['expected_implementation_site'].get('files', [])) or 'none'} symbols={', '.join(unit['expected_implementation_site'].get('symbols', [])) or 'none'}",
                    f"- Planned implementation sites: {', '.join(unit.get('planned_implementation_sites', [])) or 'none'}",
                    f"- Heuristic implementation sites: {', '.join(unit.get('heuristic_implementation_sites', [])) or 'none'}",
                    f"- Observed implementation sites: {', '.join(unit.get('observed_implementation_sites', [])) or 'none'}",
                    f"- Fidelity state: `{unit['fidelity_state']}`",
                    f"- Common failure mode: {unit['common_failure_mode']}",
                    f"- Verification level: `{unit['verification_level']}`",
                    f"- Verification note: {unit['verification_note']}",
                    "",
                ]
            )
    path = output_dir / "IMPLEMENTATION_FIDELITY.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_implementation_fidelity_pass(
    *,
    analysis_output_dir: Path,
    selected_idea: Dict[str, Any],
    atomic_bundle: Dict[str, Any],
    source_mapping: Dict[str, Any],
    code_plan: Dict[str, Any],
    experiment_manifest: Dict[str, Any],
    executed_runs: Sequence[Dict[str, Any]],
    phase: str,
) -> Dict[str, Any]:
    fidelity_units: List[Dict[str, Any]] = []
    for unit in atomic_bundle.get("atomic_units", []):
        planned_entries = planned_site_entries(unit, source_mapping=source_mapping, code_plan=code_plan)
        heuristic_entries = heuristic_site_entries(
            unit,
            selected_idea=selected_idea,
            experiment_manifest=experiment_manifest,
            executed_runs=executed_runs,
        )
        observed_entries, observed_level = observed_site_entries(unit, executed_runs)
        fidelity_state, verification_level, verification_note = unit_state(
            phase=phase,
            surface=str(unit.get("expected_code_surface") or "model"),
            planned_entries=planned_entries,
            heuristic_entries=heuristic_entries,
            observed_entries=observed_entries,
            observed_level=observed_level,
            executed_runs=executed_runs,
        )
        fidelity_units.append(
            {
                "atomic_id": unit.get("atomic_id"),
                "concept_name": unit.get("concept_name"),
                "expected_implementation_site": {
                    "surface": unit.get("expected_code_surface"),
                    "files": list(unit.get("target_file_candidates", [])),
                    "symbols": list(unit.get("target_symbol_candidates", [])),
                },
                "planned_implementation_sites": site_values(planned_entries),
                "heuristic_implementation_sites": site_values(heuristic_entries),
                "observed_implementation_sites": site_values(observed_entries),
                "actual_observed_implementation_site": site_values(observed_entries),
                "evidence_provenance": {
                    "planned": planned_entries,
                    "heuristic": heuristic_entries,
                    "observed": observed_entries,
                },
                "fidelity_state": fidelity_state,
                "common_failure_mode": common_failure_mode(unit),
                "verification_note": verification_note,
                "verification_level": verification_level,
                "verification_mode": VERIFICATION_MODE_BY_LEVEL.get(verification_level, "unknown"),
            }
        )
    payload = {
        "schema_version": "1.0",
        "status": "blocked" if atomic_bundle.get("status") == "blocked" else "ready",
        "phase": phase,
        "selected_idea_id": str(selected_idea.get("id") or ""),
        "fidelity_units": fidelity_units,
        "fidelity_summary": summarize_fidelity(fidelity_units),
        "blockers": list(atomic_bundle.get("blockers", [])),
    }
    json_path = analysis_output_dir / "IMPLEMENTATION_FIDELITY.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    markdown_path = write_fidelity_markdown(analysis_output_dir, payload)
    return {
        **payload,
        "artifact_paths": [str(markdown_path), str(json_path)],
        "artifact_path": str(json_path),
    }
