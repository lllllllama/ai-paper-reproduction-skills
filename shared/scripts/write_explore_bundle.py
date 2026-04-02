#!/usr/bin/env python3
"""Shared writer for exploratory code and exploratory run bundles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def load_context(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def bullets(items: Iterable[str]) -> str:
    values = [item for item in items if item]
    if not values:
        return "- None."
    return "\n".join(f"- {item}" for item in values)


def format_source_refs(source_repo_refs: Iterable[Dict[str, Any]]) -> List[str]:
    refs = []
    for item in source_repo_refs:
        repo = item.get("repo", "unknown")
        ref = item.get("ref", "unknown")
        note = item.get("note")
        line = f"- `{repo}` @ `{ref}`"
        if note:
            line += f": {note}"
        refs.append(line)
    return refs or ["- None."]


def current_research_value(context: Dict[str, Any]) -> str:
    return str(context.get("current_research") or context.get("baseline_ref") or "unknown")


def require_field(value: Any, field_name: str) -> Any:
    if value is None or value == "":
        raise ValueError(f"Missing required explore field: {field_name}")
    return value


def explore_context_payload(context: Dict[str, Any]) -> Dict[str, Any]:
    explicit_auth = context.get("explicit_explore_authorization")
    raw = dict(context.get("explore_context", {}))
    current_research = str(raw.get("current_research") or current_research_value(context))
    experiment_branch = str(raw.get("experiment_branch") or context.get("experiment_branch") or "")
    return {
        "context_id": raw.get("context_id") or context.get("context_id"),
        "current_research": require_field(current_research, "current_research"),
        "experiment_branch": require_field(experiment_branch, "experiment_branch"),
        "explicit_explore_authorization": require_field(
            raw.get("explicit_explore_authorization", explicit_auth),
            "explicit_explore_authorization",
        ),
        "isolated_workspace": raw.get("isolated_workspace", context.get("isolated_workspace", True)),
        "workspace_mode": raw.get("workspace_mode", context.get("workspace_mode")),
        "workspace_root": raw.get("workspace_root", context.get("workspace_root")),
    }


def format_stage_trace(stage_trace: Iterable[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    for item in stage_trace:
        stage = item.get("stage", "unknown")
        status = item.get("status", "unknown")
        tool = item.get("tool")
        summary = item.get("summary")
        line = f"- `{stage}` [{status}]"
        if tool:
            line += f" via `{tool}`"
        if summary:
            line += f": {summary}"
        lines.append(line)
    return lines or ["- None."]


def write_changeset(output_dir: Path, context: Dict[str, Any], mode: str) -> None:
    explore_context = explore_context_payload(context)
    title = "# Explore Changeset"
    if mode == "code":
        intent_title = "## Exploratory code focus"
    elif mode == "run":
        intent_title = "## Experiment focus"
    else:
        intent_title = "## Research exploration focus"
    lines = [
        title,
        "",
        f"- Mode: `{mode}`",
        f"- Current research: `{explore_context['current_research']}`",
        f"- Experiment branch: `{explore_context['experiment_branch']}`",
        f"- Isolated workspace: `{explore_context['isolated_workspace']}`",
        f"- Workspace mode: `{explore_context.get('workspace_mode') or 'unknown'}`",
        f"- Trusted promotion candidate: `{context.get('trusted_promote_candidate', False)}`",
        "",
        "## Source references",
        "",
        *format_source_refs(context.get("source_repo_refs", [])),
        "",
        "## Helper stage trace",
        "",
        *format_stage_trace(context.get("helper_stage_trace", [])),
        "",
        intent_title,
        "",
        bullets(context.get("changes_summary", [])),
        "",
        "## Notes",
        "",
        bullets(context.get("notes", [])),
        "",
    ]
    (output_dir / "CHANGESET.md").write_text("\n".join(lines), encoding="utf-8")


def write_top_runs(output_dir: Path, context: Dict[str, Any], mode: str) -> None:
    explore_context = explore_context_payload(context)
    metric_policy = context.get("metric_policy", {})
    variant_budget = context.get("variant_budget", {})
    selection_policy = context.get("selection_policy", {})
    lines = [
        "# Top Runs",
        "",
        f"- Raw variant count: `{context.get('raw_variant_count', context.get('variant_count', 0))}`",
        f"- Variant count: `{context.get('variant_count', 0)}`",
        f"- Pruned variant count: `{context.get('pruned_variant_count', 0)}`",
        f"- Current research: `{explore_context['current_research']}`",
        "",
    ]
    if selection_policy.get("factors"):
        factor_list = ", ".join(selection_policy.get("factors", []))
        lines.extend(
            [
                f"- Pre-execution selection factors: `{factor_list}`",
                "",
            ]
        )
    if metric_policy.get("primary_metric"):
        lines.extend(
            [
                f"- Ranking metric: `{metric_policy['primary_metric']}` ({metric_policy.get('metric_goal', 'maximize')})",
                "",
            ]
        )
    if variant_budget.get("max_variants") or variant_budget.get("max_short_cycle_runs"):
        lines.extend(
            [
                f"- Budget: max_variants=`{variant_budget.get('max_variants', 0)}`, max_short_cycle_runs=`{variant_budget.get('max_short_cycle_runs', 0)}`",
                "",
            ]
        )
    lines.extend(
        [
        "## Candidate hypotheses",
        "",
        bullets(context.get("candidate_hypotheses", [])),
        "",
        "## Best runs",
        "",
        ]
    )
    best_runs = context.get("best_runs", [])
    if not best_runs:
        lines.append("- None.")
    else:
        for item in best_runs:
            best_metric = item.get("best_metric")
            ranking_metric = item.get("ranking_metric")
            parts = [f"- `{item.get('id', 'unknown')}`"]
            if isinstance(best_metric, dict) and best_metric.get("name") and best_metric.get("value") is not None:
                parts.append(f"best_metric=`{best_metric['name']}={best_metric['value']}`")
            elif item.get("metric") is not None:
                parts.append(f"metric=`{item.get('metric', 'unknown')}`")
            if isinstance(ranking_metric, dict) and ranking_metric.get("name") and ranking_metric.get("value") is not None:
                parts.append(
                    f"ranking_metric=`{ranking_metric['name']}={ranking_metric['value']}` ({ranking_metric.get('goal', 'maximize')})"
                )
            parts.append(f"summary={item.get('summary', 'none')}")
            lines.append(
                " ".join(parts)
            )
    lines.extend(
        [
            "",
            "## Recommended next trials",
            "",
            bullets(context.get("recommended_next_trials", [])),
            "",
        ]
    )
    if mode in {"run", "research"}:
        lines.extend(
            [
                "## Execution notes",
                "",
                bullets(context.get("execution_notes", [])),
                "",
            ]
        )
    (output_dir / "TOP_RUNS.md").write_text("\n".join(lines), encoding="utf-8")


def write_status(output_dir: Path, context: Dict[str, Any], mode: str) -> None:
    explore_context = explore_context_payload(context)
    current_research = explore_context["current_research"]
    payload = {
        "schema_version": context.get("schema_version", "1.0"),
        "context_id": context.get("context_id") or explore_context.get("context_id"),
        "mode": mode,
        "status": context.get("status", "planned"),
        "current_research": current_research,
        "baseline_ref": context.get("baseline_ref", current_research),
        "experiment_branch": explore_context["experiment_branch"],
        "isolated_workspace": explore_context["isolated_workspace"],
        "explore_context": explore_context,
        "source_repo_refs": context.get("source_repo_refs", []),
        "raw_variant_count": context.get("raw_variant_count", context.get("variant_count", 0)),
        "variant_count": context.get("variant_count", 0),
        "pruned_variant_count": context.get("pruned_variant_count", 0),
        "variant_budget": context.get("variant_budget", {"max_variants": 0, "max_short_cycle_runs": 0}),
        "selection_policy": context.get("selection_policy", {}),
        "metric_policy": context.get("metric_policy", {"primary_metric": None, "metric_goal": "maximize"}),
        "best_runs": context.get("best_runs", []),
        "candidate_edit_targets": context.get("candidate_edit_targets", []),
        "code_tracks": context.get("code_tracks", []),
        "candidate_hypotheses": context.get("candidate_hypotheses", []),
        "planned_skill_chain": context.get("planned_skill_chain", []),
        "helper_stage_trace": context.get("helper_stage_trace", []),
        "recommended_next_trials": context.get("recommended_next_trials", []),
        "execution_notes": context.get("execution_notes", []),
        "trusted_promote_candidate": context.get("trusted_promote_candidate", False),
        "explicit_explore_authorization": explore_context["explicit_explore_authorization"],
        "outputs": {
            "changeset": "explore_outputs/CHANGESET.md",
            "top_runs": "explore_outputs/TOP_RUNS.md",
            "status": "explore_outputs/status.json",
        },
        "notes": context.get("notes", []),
    }
    (output_dir / "status.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_bundle(mode: str, output_dir: Path, context: Dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_changeset(output_dir, context, mode)
    write_top_runs(output_dir, context, mode)
    write_status(output_dir, context, mode)


def main(default_mode: str = "code", default_output_dir: Optional[str] = None) -> int:
    parser = argparse.ArgumentParser(description="Write exploratory output bundles.")
    parser.add_argument("--context-json", required=True, help="Path to a context JSON file.")
    parser.add_argument("--mode", choices=["code", "run", "research"], default=default_mode)
    parser.add_argument(
        "--output-dir",
        default=default_output_dir or "explore_outputs",
        help="Directory where output files will be written.",
    )
    args = parser.parse_args()

    context = load_context(Path(args.context_json).resolve())
    write_bundle(args.mode, Path(args.output_dir).resolve(), context)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
