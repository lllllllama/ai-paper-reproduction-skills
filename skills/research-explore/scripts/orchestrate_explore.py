#!/usr/bin/env python3
"""Plan explicit exploratory research work on top of current_research."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple


def run_json(script: Path, args: List[str]) -> Dict[str, Any]:
    result = subprocess.run([sys.executable, str(script), *args], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def write_bundle(script: Path, output_dir: Path, context: Dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
        context_path = Path(handle.name)
        handle.write(json.dumps(context, indent=2, ensure_ascii=False))

    try:
        subprocess.run(
            [
                sys.executable,
                str(script),
                "--context-json",
                str(context_path),
                "--output-dir",
                str(output_dir),
            ],
            check=True,
        )
    finally:
        if context_path.exists():
            context_path.unlink()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:40] or "current-research"


def choose_experiment_branch(current_research: str, explicit_branch: str) -> str:
    if explicit_branch:
        return explicit_branch
    return f"exp/research-explore-{slugify(current_research)}"


def load_variant_spec(path: Path, current_research: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    spec = json.loads(path.read_text(encoding="utf-8-sig"))
    explicit_value = spec.get("current_research") or spec.get("baseline_ref")
    if explicit_value and explicit_value != current_research:
        raise ValueError(
            f"Variant spec current research `{explicit_value}` does not match --current-research `{current_research}`."
        )
    spec["current_research"] = current_research
    spec.setdefault("baseline_ref", current_research)
    return spec, spec


def build_variant_matrix(planner_script: Path, variant_spec_json: str, current_research: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if not variant_spec_json:
        empty_spec = {"current_research": current_research, "baseline_ref": current_research}
        empty_matrix = {
            "schema_version": "1.0",
            "current_research": current_research,
            "baseline_ref": current_research,
            "base_command": None,
            "variant_count": 0,
            "variants": [],
        }
        return empty_matrix, empty_spec

    spec_path = Path(variant_spec_json).resolve()
    spec, normalized_spec = load_variant_spec(spec_path, current_research)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
        temp_spec_path = Path(handle.name)
        handle.write(json.dumps(normalized_spec, indent=2, ensure_ascii=False))

    try:
        matrix = run_json(planner_script, ["--spec-json", str(temp_spec_path), "--json"])
    finally:
        if temp_spec_path.exists():
            temp_spec_path.unlink()

    return matrix, spec


def build_candidate_hypotheses(spec: Dict[str, Any], analysis_data: Dict[str, Any]) -> List[str]:
    hypotheses: List[str] = []
    for axis, values in sorted(spec.get("variant_axes", {}).items()):
        shown_values = ", ".join(str(value) for value in values[:3])
        hypotheses.append(f"Probe `{axis}` variation across: {shown_values}.")
    if spec.get("base_command"):
        hypotheses.append(f"Keep `{spec['base_command']}` as the execution anchor for candidate trials.")
    for suggestion in analysis_data.get("conservative_suggestions", [])[:2]:
        hypotheses.append(suggestion)
    if not hypotheses:
        hypotheses.append("Start with one low-risk exploratory code change plus one short-cycle candidate run.")
    return hypotheses[:5]


def build_recommended_next_trials(
    variant_matrix: Dict[str, Any],
    setup_plan: Dict[str, Any],
    analysis_data: Dict[str, Any],
) -> List[str]:
    trials: List[str] = []
    for item in variant_matrix.get("variants", [])[:3]:
        axes = ", ".join(f"{key}={value}" for key, value in sorted(item.get("axes", {}).items())) or "no axis overrides"
        subset = item.get("subset_size") if item.get("subset_size") is not None else "full-data"
        steps = item.get("short_run_steps") if item.get("short_run_steps") is not None else "documented schedule"
        trials.append(f"Run `{item['id']}` with {axes}, subset={subset}, steps={steps}.")
    for item in setup_plan.get("unresolved_setup_risks", [])[:1]:
        trials.append(f"Resolve setup risk before scaling out: {item}")
    for item in analysis_data.get("conservative_suggestions", [])[:1]:
        trials.append(item)
    if not trials:
        trials.append("Confirm one isolated candidate branch and run one short-cycle check before broader exploration.")
    return trials[:5]


def build_changes_summary(
    current_research: str,
    experiment_branch: str,
    planned_skill_chain: List[str],
    variant_matrix: Dict[str, Any],
    include_analysis_pass: bool,
    include_setup_pass: bool,
) -> List[str]:
    summary = [
        f"Anchored exploratory work to `current_research={current_research}`.",
        f"Reserved isolated experiment branch `{experiment_branch}` for candidate-only work.",
        f"Planned orchestrator chain: {', '.join(planned_skill_chain)}.",
    ]
    if include_analysis_pass:
        summary.append("Included a read-only analysis pass before wider exploratory edits.")
    if include_setup_pass:
        summary.append("Included a setup planning pass to preserve environment and asset assumptions.")
    if variant_matrix.get("variant_count"):
        summary.append(f"Prepared `{variant_matrix['variant_count']}` exploratory run candidates from the variant matrix.")
    return summary


def build_execution_notes(
    scan_data: Dict[str, Any],
    setup_plan: Dict[str, Any],
    analysis_data: Dict[str, Any],
    variant_matrix: Dict[str, Any],
) -> List[str]:
    notes: List[str] = []
    if scan_data.get("readme_path"):
        notes.append(f"Repository README: `{scan_data['readme_path']}`.")
    if setup_plan.get("environment_file"):
        notes.append(f"Environment plan source: `{setup_plan['environment_file']}`.")
    if variant_matrix.get("base_command"):
        notes.append(f"Base command: `{variant_matrix['base_command']}`.")
    suspicious = analysis_data.get("suspicious_patterns", [])
    if suspicious:
        notes.append(f"Analysis surfaced `{len(suspicious)}` suspicious pattern hints for review before heavier exploration.")
    if variant_matrix.get("variant_count"):
        notes.append("Prefer short-cycle candidate ranking before widening exploratory runs.")
    return notes


def build_context(
    *,
    repo_path: Path,
    current_research: str,
    experiment_branch: str,
    scan_data: Dict[str, Any],
    setup_plan: Dict[str, Any],
    analysis_data: Dict[str, Any],
    variant_matrix: Dict[str, Any],
    variant_spec: Dict[str, Any],
    planned_skill_chain: List[str],
    include_analysis_pass: bool,
    include_setup_pass: bool,
) -> Dict[str, Any]:
    return {
        "schema_version": "1.0",
        "status": "planned",
        "current_research": current_research,
        "baseline_ref": current_research,
        "experiment_branch": experiment_branch,
        "isolated_workspace": True,
        "source_repo_refs": [
            {
                "repo": repo_path.name,
                "ref": current_research,
                "note": "current_research anchor",
            }
        ],
        "variant_count": variant_matrix.get("variant_count", 0),
        "best_runs": [],
        "candidate_hypotheses": build_candidate_hypotheses(variant_spec, analysis_data),
        "planned_skill_chain": planned_skill_chain,
        "recommended_next_trials": build_recommended_next_trials(variant_matrix, setup_plan, analysis_data),
        "trusted_promote_candidate": False,
        "explicit_explore_authorization": True,
        "changes_summary": build_changes_summary(
            current_research,
            experiment_branch,
            planned_skill_chain,
            variant_matrix,
            include_analysis_pass,
            include_setup_pass,
        ),
        "execution_notes": build_execution_notes(scan_data, setup_plan, analysis_data, variant_matrix),
        "notes": [
            "Exploratory result only; do not present this as trusted reproduction success.",
            "`current_research` should map to a durable branch, commit, checkpoint, run record, or trained model state.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan explicit exploratory research work on top of current_research.")
    parser.add_argument("--repo", required=True, help="Path to the target repository.")
    parser.add_argument("--current-research", required=True, help="Durable identifier for the current research context.")
    parser.add_argument("--output-dir", default="explore_outputs", help="Directory to write exploratory outputs into.")
    parser.add_argument("--experiment-branch", default="", help="Optional experiment branch or worktree label.")
    parser.add_argument("--variant-spec-json", default="", help="Optional path to a variant-spec JSON file.")
    parser.add_argument("--include-analysis-pass", action="store_true", help="Include analyze-project in the planned chain.")
    parser.add_argument("--include-setup-pass", action="store_true", help="Include env-and-assets-bootstrap in the planned chain.")
    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()
    base_dir = Path(__file__).resolve().parents[2]
    scan_script = base_dir / "repo-intake-and-plan" / "scripts" / "scan_repo.py"
    setup_script = base_dir / "env-and-assets-bootstrap" / "scripts" / "plan_setup.py"
    analysis_script = base_dir / "analyze-project" / "scripts" / "analyze_project.py"
    planner_script = base_dir / "explore-run" / "scripts" / "plan_variants.py"
    writer_script = Path(__file__).resolve().parent / "write_outputs.py"

    scan_data = run_json(scan_script, ["--repo", str(repo_path), "--json"])
    setup_plan = run_json(setup_script, ["--repo", str(repo_path), "--json"]) if args.include_setup_pass else {}
    analysis_data = run_json(analysis_script, ["--repo", str(repo_path), "--json"]) if args.include_analysis_pass else {}
    variant_matrix, variant_spec = build_variant_matrix(planner_script, args.variant_spec_json, args.current_research)

    planned_skill_chain: List[str] = []
    if args.include_analysis_pass:
        planned_skill_chain.append("analyze-project")
    if args.include_setup_pass:
        planned_skill_chain.append("env-and-assets-bootstrap")
    planned_skill_chain.extend(["explore-code", "explore-run"])

    experiment_branch = choose_experiment_branch(args.current_research, args.experiment_branch)
    context = build_context(
        repo_path=repo_path,
        current_research=args.current_research,
        experiment_branch=experiment_branch,
        scan_data=scan_data,
        setup_plan=setup_plan,
        analysis_data=analysis_data,
        variant_matrix=variant_matrix,
        variant_spec=variant_spec,
        planned_skill_chain=planned_skill_chain,
        include_analysis_pass=args.include_analysis_pass,
        include_setup_pass=args.include_setup_pass,
    )

    output_dir = Path(args.output_dir).resolve()
    write_bundle(writer_script, output_dir, context)

    payload = {
        "schema_version": "1.0",
        "repo": str(repo_path),
        "current_research": args.current_research,
        "experiment_branch": experiment_branch,
        "planned_skill_chain": planned_skill_chain,
        "variant_count": context["variant_count"],
        "candidate_hypotheses": context["candidate_hypotheses"],
        "recommended_next_trials": context["recommended_next_trials"],
        "setup_commands": setup_plan.get("setup_commands", []),
        "setup_notes": setup_plan.get("setup_notes", []),
        "analysis_summary": analysis_data.get("summary_lines", []),
        "analysis_suspicious_patterns": analysis_data.get("suspicious_patterns", []),
        "base_command": variant_matrix.get("base_command"),
        "output_dir": str(output_dir),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
