#!/usr/bin/env python3
"""Plan explicit exploratory research work on top of current_research."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DURABLE_ANCHOR_HASH_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
EXTERNAL_REFERENCE_PREFIXES = ("run:", "checkpoint:", "branch:", "commit:", "model:", "state:")


def run_json(script: Path, args: List[str]) -> Dict[str, Any]:
    result = subprocess.run([sys.executable, str(script), *args], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def run_text(command: List[str], cwd: Optional[Path] = None) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True, cwd=str(cwd) if cwd else None)
    return result.stdout.strip()


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


def maybe_git_root(repo_path: Path) -> Optional[Path]:
    try:
        return Path(run_text(["git", "rev-parse", "--show-toplevel"], cwd=repo_path)).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def build_context_id(current_research: str, experiment_branch: str) -> str:
    digest = hashlib.sha1(f"{current_research}::{experiment_branch}".encode("utf-8")).hexdigest()[:12]
    return f"research-explore-{digest}"


def experiment_worktree_root(git_root: Path, experiment_branch: str) -> Path:
    base_dir = git_root.parent / f".{git_root.name}-explore-worktrees" / slugify(experiment_branch)
    return base_dir / git_root.name


def validate_current_research(repo_path: Path, current_research: str) -> Dict[str, Any]:
    value = current_research.strip()
    if not value:
        raise ValueError("`current_research` is required.")

    literal_path = Path(value)
    if literal_path.is_absolute() and literal_path.exists():
        return {"kind": "path", "value": value, "resolved_path": str(literal_path.resolve())}

    repo_relative = (repo_path / value).resolve()
    if repo_relative.exists():
        return {"kind": "repo-path", "value": value, "resolved_path": str(repo_relative)}

    git_root = maybe_git_root(repo_path)
    if git_root:
        try:
            resolved_ref = run_text(["git", "rev-parse", "--verify", f"{value}^{{commit}}"], cwd=git_root)
            return {
                "kind": "git-ref",
                "value": value,
                "resolved_ref": resolved_ref,
                "git_root": str(git_root),
            }
        except subprocess.CalledProcessError:
            pass

    if "@" in value:
        left, _, right = value.partition("@")
        if left and right and (
            DURABLE_ANCHOR_HASH_RE.fullmatch(right.strip())
            or any(right.strip().startswith(prefix) for prefix in EXTERNAL_REFERENCE_PREFIXES)
        ):
            return {"kind": "named-anchor", "value": value}

    raise ValueError(
        "`current_research` should map to a durable branch, commit, checkpoint, run record, or trained model state."
    )


def validate_existing_worktree(worktree_root: Path, expected_branch: str) -> Dict[str, Any]:
    actual_root = Path(run_text(["git", "rev-parse", "--show-toplevel"], cwd=worktree_root)).resolve()
    actual_branch = run_text(["git", "symbolic-ref", "--quiet", "--short", "HEAD"], cwd=worktree_root)
    if actual_root != worktree_root.resolve():
        raise ValueError(
            f"Existing experiment workspace `{worktree_root}` is not a valid git worktree root."
        )
    if actual_branch != expected_branch:
        raise ValueError(
            f"Existing experiment workspace `{worktree_root}` is on branch `{actual_branch}`, expected `{expected_branch}`."
        )
    return {
        "workspace_root": str(actual_root),
        "worktree_root": str(actual_root),
        "mode": "worktree",
    }


def ensure_experiment_workspace(repo_path: Path, experiment_branch: str) -> Dict[str, Any]:
    git_root = maybe_git_root(repo_path)
    if git_root is None:
        raise ValueError("Explore orchestration requires a git repository so the isolated experiment branch can be created.")

    head_sha = run_text(["git", "rev-parse", "HEAD"], cwd=git_root)
    try:
        current_branch = run_text(["git", "symbolic-ref", "--quiet", "--short", "HEAD"], cwd=git_root)
    except subprocess.CalledProcessError:
        current_branch = "DETACHED"

    branch_ref = f"refs/heads/{experiment_branch}"
    created_branch = False
    try:
        branch_sha = run_text(["git", "rev-parse", "--verify", branch_ref], cwd=git_root)
        branch_exists = True
    except subprocess.CalledProcessError:
        branch_sha = head_sha
        branch_exists = False

    if current_branch == experiment_branch:
        isolated_workspace = experiment_branch.startswith(("exp/", "explore/"))
        return {
            "mode": "branch",
            "workspace_root": str(git_root),
            "worktree_root": None,
            "branch": experiment_branch,
            "branch_ref": branch_ref,
            "branch_sha": branch_sha,
            "head_sha": head_sha,
            "current_branch": current_branch,
            "created_branch": created_branch,
            "isolated_workspace": isolated_workspace,
        }

    worktree_root = experiment_worktree_root(git_root, experiment_branch)
    if worktree_root.exists():
        worktree_info = validate_existing_worktree(worktree_root, experiment_branch)
    else:
        worktree_root.parent.mkdir(parents=True, exist_ok=True)
        if branch_exists:
            run_text(["git", "worktree", "add", str(worktree_root), experiment_branch], cwd=git_root)
        else:
            run_text(["git", "worktree", "add", "-b", experiment_branch, str(worktree_root), head_sha], cwd=git_root)
            created_branch = True
            branch_exists = True
        branch_sha = run_text(["git", "rev-parse", "--verify", branch_ref], cwd=git_root)
        worktree_info = validate_existing_worktree(worktree_root, experiment_branch)

    return {
        "mode": worktree_info["mode"],
        "workspace_root": worktree_info["workspace_root"],
        "worktree_root": worktree_info["worktree_root"],
        "branch": experiment_branch,
        "branch_ref": branch_ref,
        "branch_sha": branch_sha,
        "head_sha": head_sha,
        "current_branch": current_branch,
        "created_branch": created_branch,
        "isolated_workspace": True,
    }


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
            "raw_variant_count": 0,
            "variant_count": 0,
            "pruned_variant_count": 0,
            "variant_budget": {
                "max_variants": 0,
                "max_short_cycle_runs": 0,
            },
            "metric_policy": {
                "primary_metric": None,
                "metric_goal": "maximize",
            },
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


def build_stage_trace_entry(stage: str, tool: str, summary: str, status: str = "completed") -> Dict[str, Any]:
    return {
        "stage": stage,
        "tool": tool,
        "status": status,
        "summary": summary,
    }


def normalize_flag_name(key: str) -> str:
    return "--" + re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-")


def quote_cli_value(value: Any) -> str:
    text = str(value)
    if any(char.isspace() for char in text):
        return f"\"{text}\""
    return text


def maybe_append_cli_arg(command: str, flag: Any, value: Any) -> str:
    if flag in {None, False, ""} or value is None:
        return command
    return f"{command} {flag} {quote_cli_value(value)}"


def compose_variant_command(base_command: str, variant: Dict[str, Any], spec: Dict[str, Any]) -> str:
    command = base_command.strip()
    axis_flag_map = spec.get("axis_flag_map", {})
    for key, value in sorted(variant.get("axes", {}).items()):
        flag = axis_flag_map.get(key) or normalize_flag_name(key)
        command = maybe_append_cli_arg(command, flag, value)

    command = maybe_append_cli_arg(command, spec.get("subset_size_flag", "--subset-size"), variant.get("subset_size"))
    command = maybe_append_cli_arg(command, spec.get("short_run_steps_flag", "--max-steps"), variant.get("short_run_steps"))
    return command


def summarize_variant_result(result: Dict[str, Any]) -> str:
    metric = result.get("best_metric")
    if metric:
        return f"status={result.get('status', 'unknown')}, stop={result.get('stop_reason', 'unknown')}, metric={metric['name']}={metric['value']}"
    return f"status={result.get('status', 'unknown')}, stop={result.get('stop_reason', 'unknown')}"


def infer_execution_kind(base_command: str, spec: Dict[str, Any]) -> str:
    explicit = str(spec.get("execution_kind") or "").strip().lower()
    if explicit in {"train", "training"}:
        return "training"
    if explicit in {"run", "verify", "eval", "inference", "non_training", "non-training"}:
        return "non_training"

    lowered = base_command.lower()
    if any(token in lowered for token in [" train", "trainer", "fit", "fine-tune", "finetune"]):
        return "training"
    return "non_training"


def normalize_metric_goal(value: Any) -> str:
    text = str(value or "maximize").strip().lower()
    if text in {"min", "minimize", "lower", "lower_is_better"}:
        return "minimize"
    return "maximize"


def safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except ValueError:
        return None


def extract_metric_policy(variant_matrix: Dict[str, Any], variant_spec: Dict[str, Any]) -> Dict[str, Any]:
    matrix_policy = dict(variant_matrix.get("metric_policy", {}))
    primary_metric = matrix_policy.get("primary_metric") or variant_spec.get("primary_metric")
    metric_goal = normalize_metric_goal(matrix_policy.get("metric_goal") or variant_spec.get("metric_goal"))
    return {
        "primary_metric": primary_metric,
        "metric_goal": metric_goal,
    }


def default_metric_payload(item: Dict[str, Any]) -> Tuple[Optional[float], Optional[str]]:
    metric = item.get("best_metric")
    if isinstance(metric, dict):
        return safe_float(metric.get("value")), metric.get("name")
    return None, None


def metric_payload_for_policy(item: Dict[str, Any], primary_metric: Optional[str]) -> Tuple[Optional[float], Optional[str], bool]:
    observed_metrics = item.get("observed_metrics", {})
    if primary_metric and isinstance(observed_metrics, dict) and primary_metric in observed_metrics:
        return safe_float(observed_metrics[primary_metric]), primary_metric, True

    best_metric = item.get("best_metric")
    if primary_metric and isinstance(best_metric, dict) and best_metric.get("name") == primary_metric:
        return safe_float(best_metric.get("value")), primary_metric, True

    fallback_value, fallback_name = default_metric_payload(item)
    return fallback_value, fallback_name, False


def decorate_run_with_metric_policy(item: Dict[str, Any], metric_policy: Dict[str, Any]) -> Dict[str, Any]:
    primary_metric = metric_policy.get("primary_metric")
    metric_goal = normalize_metric_goal(metric_policy.get("metric_goal"))
    ranking_value, ranking_name, matched_primary_metric = metric_payload_for_policy(item, primary_metric)

    decorated = dict(item)
    decorated["ranking_metric"] = (
        {
            "name": ranking_name,
            "value": ranking_value,
            "goal": metric_goal,
        }
        if ranking_name and ranking_value is not None
        else None
    )
    decorated["ranking_metric_name"] = ranking_name
    decorated["ranking_metric_goal"] = metric_goal
    decorated["matched_primary_metric"] = matched_primary_metric if primary_metric else ranking_value is not None
    decorated["metric_policy_applied"] = bool(primary_metric)
    return decorated


def rank_executed_runs(executed_runs: List[Dict[str, Any]], metric_policy: Dict[str, Any]) -> List[Dict[str, Any]]:
    status_rank = {"success": 3, "partial": 2, "blocked": 1, "not_run": 0}
    primary_metric = metric_policy.get("primary_metric")
    metric_goal = normalize_metric_goal(metric_policy.get("metric_goal"))

    def adjust_for_goal(value: Optional[float]) -> float:
        numeric_value = safe_float(value)
        if numeric_value is None:
            return float("-inf")
        return numeric_value if metric_goal == "maximize" else -numeric_value

    decorated = [decorate_run_with_metric_policy(item, metric_policy) for item in executed_runs]

    def sort_key(item: Dict[str, Any]) -> Tuple[int, int, float, float]:
        ranking_metric = item.get("ranking_metric")
        ranking_value = ranking_metric.get("value") if isinstance(ranking_metric, dict) else None
        fallback_value, _fallback_name = default_metric_payload(item)
        return (
            status_rank.get(item.get("status", "not_run"), 0),
            1 if item.get("matched_primary_metric") else 0,
            adjust_for_goal(ranking_value) if primary_metric else adjust_for_goal(ranking_value),
            adjust_for_goal(fallback_value),
        )

    return sorted(decorated, key=sort_key, reverse=True)


def execute_variant_candidates(
    *,
    train_execute_script: Path,
    run_execute_script: Path,
    repo_path: Path,
    variant_matrix: Dict[str, Any],
    variant_spec: Dict[str, Any],
    current_research: str,
    timeout: int,
    max_executed_variants: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    base_command = variant_matrix.get("base_command")
    variants = variant_matrix.get("variants", [])
    if not base_command or not variants or max_executed_variants <= 0:
        return [], []

    execution_kind = infer_execution_kind(base_command, variant_spec)
    metric_policy = extract_metric_policy(variant_matrix, variant_spec)
    executed_runs: List[Dict[str, Any]] = []
    stage_trace: List[Dict[str, Any]] = []
    for variant in variants[:max_executed_variants]:
        command = compose_variant_command(base_command, variant, variant_spec)
        if execution_kind == "training":
            run_mode = "short_run_verification" if variant.get("short_run_steps") is not None else "startup_verification"
            payload = run_json(
                train_execute_script,
                [
                    "--repo",
                    str(repo_path),
                    "--command",
                    command,
                    "--timeout",
                    str(timeout),
                    "--lane",
                    "explore",
                    "--run-mode",
                    run_mode,
                    "--dataset",
                    "current_research",
                    "--checkpoint-source",
                    current_research,
                    "--max-steps",
                    str(variant.get("short_run_steps") or 0),
                ],
            )
            tool_name = "run-train/scripts/run_training.py"
        else:
            run_mode = "candidate_verify"
            payload = run_json(
                run_execute_script,
                [
                    "--repo",
                    str(repo_path),
                    "--command",
                    command,
                    "--timeout",
                    str(timeout),
                ],
            )
            payload.setdefault("stop_reason", "command_completed" if payload.get("status") == "success" else "command_checked")
            tool_name = "minimal-run-and-audit/scripts/run_command.py"
        summary = summarize_variant_result(payload)
        executed_runs.append(
            {
                "id": variant.get("id", "unknown"),
                "metric": payload.get("best_metric", {}).get("value") if payload.get("best_metric") else payload.get("status", "unknown"),
                "metric_name": payload.get("best_metric", {}).get("name") if payload.get("best_metric") else None,
                "summary": summary,
                "status": payload.get("status", "unknown"),
                "stop_reason": payload.get("stop_reason", "unknown"),
                "command": command,
                "axes": variant.get("axes", {}),
                "subset_size": variant.get("subset_size"),
                "short_run_steps": variant.get("short_run_steps"),
                "best_metric": payload.get("best_metric"),
                "observed_metrics": payload.get("observed_metrics", {}),
                "best_checkpoint": payload.get("best_checkpoint"),
            }
        )
        stage_trace.append(
            build_stage_trace_entry(
                "variant-execution",
                tool_name,
                f"Executed `{variant.get('id', 'unknown')}` with mode `{run_mode}` and observed {summary}.",
            )
        )

    return rank_executed_runs(executed_runs, metric_policy), stage_trace


def build_candidate_hypotheses(spec: Dict[str, Any], analysis_data: Dict[str, Any], code_plan: Dict[str, Any]) -> List[str]:
    hypotheses: List[str] = []
    for axis, values in sorted(spec.get("variant_axes", {}).items()):
        shown_values = ", ".join(str(value) for value in values[:3])
        hypotheses.append(f"Probe `{axis}` variation across: {shown_values}.")
    if spec.get("base_command"):
        hypotheses.append(f"Keep `{spec['base_command']}` as the execution anchor for candidate trials.")
    for track in code_plan.get("proposed_code_tracks", [])[:2]:
        hypotheses.append(track)
    for suggestion in analysis_data.get("conservative_suggestions", [])[:2]:
        hypotheses.append(suggestion)
    if not hypotheses:
        hypotheses.append("Start with one low-risk exploratory code change plus one short-cycle candidate run.")
    return hypotheses[:5]


def build_recommended_next_trials(
    variant_matrix: Dict[str, Any],
    metric_policy: Dict[str, Any],
    setup_plan: Dict[str, Any],
    analysis_data: Dict[str, Any],
    code_plan: Dict[str, Any],
    executed_runs: List[Dict[str, Any]],
) -> List[str]:
    trials: List[str] = []
    for item in executed_runs[:1]:
        metric = item.get("best_metric")
        if metric:
            trials.append(
                f"Inspect `{item['id']}` further because `{metric['name']}={metric['value']}` under exploratory execution."
            )
        else:
            trials.append(f"Review `{item['id']}` logs before launching broader candidate runs.")
    if metric_policy.get("primary_metric"):
        trials.append(
            f"Rank follow-up work by `{metric_policy['primary_metric']}` ({metric_policy['metric_goal']}) before widening the search."
        )
    for target in code_plan.get("candidate_edit_targets", [])[:1]:
        trials.append(f"Review `{target}` before widening exploratory code changes.")
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
    context_id: str,
    current_research: str,
    experiment_branch: str,
    workspace_info: Dict[str, Any],
    code_plan: Dict[str, Any],
    executed_runs: List[Dict[str, Any]],
    planned_skill_chain: List[str],
    variant_matrix: Dict[str, Any],
    metric_policy: Dict[str, Any],
    include_analysis_pass: bool,
    include_setup_pass: bool,
) -> List[str]:
    summary = [
        f"Context id: `{context_id}`.",
        f"Anchored exploratory work to `current_research={current_research}`.",
        f"Validated isolated experiment branch `{experiment_branch}` in `{workspace_info['workspace_root']}`.",
        f"Planned orchestrator chain: {', '.join(planned_skill_chain)}.",
    ]
    if workspace_info.get("created_branch"):
        summary.append(f"Created experiment branch `{experiment_branch}` from `{workspace_info['head_sha']}`.")
    if include_analysis_pass:
        summary.append("Included a read-only analysis pass before wider exploratory edits.")
    if include_setup_pass:
        summary.append("Included a setup planning pass to preserve environment and asset assumptions.")
    for track in code_plan.get("proposed_code_tracks", [])[:2]:
        summary.append(track)
    if variant_matrix.get("variant_count"):
        summary.append(f"Prepared `{variant_matrix['variant_count']}` exploratory run candidates from the variant matrix.")
    if variant_matrix.get("pruned_variant_count"):
        summary.append(
            f"Pruned `{variant_matrix['pruned_variant_count']}` higher-cost candidates under the explore-run budget policy."
        )
    if variant_matrix.get("selection_policy", {}).get("factors"):
        summary.append(
            "Pre-execution candidate selection used `cost`, `success_rate`, and `expected_gain` as the primary factors."
        )
    if metric_policy.get("primary_metric"):
        summary.append(
            f"Configured candidate ranking around `{metric_policy['primary_metric']}` with goal `{metric_policy['metric_goal']}`."
        )
    if executed_runs:
        summary.append(f"Executed `{len(executed_runs)}` exploratory candidate runs through controlled helper handoff.")
    return summary


def build_execution_notes(
    workspace_info: Dict[str, Any],
    scan_data: Dict[str, Any],
    setup_plan: Dict[str, Any],
    analysis_data: Dict[str, Any],
    code_plan: Dict[str, Any],
    variant_matrix: Dict[str, Any],
    metric_policy: Dict[str, Any],
    executed_runs: List[Dict[str, Any]],
) -> List[str]:
    notes: List[str] = []
    notes.append(
        f"Workspace mode: `{workspace_info['mode']}` on branch `{workspace_info['branch']}` (current branch before orchestration: `{workspace_info['current_branch']}`)."
    )
    if scan_data.get("readme_path"):
        notes.append(f"Repository README: `{scan_data['readme_path']}`.")
    if setup_plan.get("environment_file"):
        notes.append(f"Environment plan source: `{setup_plan['environment_file']}`.")
    targets = code_plan.get("candidate_edit_targets", [])
    if targets:
        notes.append(f"Primary code targets: {', '.join(targets[:3])}.")
    if variant_matrix.get("base_command"):
        notes.append(f"Base command: `{variant_matrix['base_command']}`.")
    suspicious = analysis_data.get("suspicious_patterns", [])
    if suspicious:
        notes.append(f"Analysis surfaced `{len(suspicious)}` suspicious pattern hints for review before heavier exploration.")
    if variant_matrix.get("variant_count"):
        notes.append("Prefer short-cycle candidate ranking before widening exploratory runs.")
    if variant_matrix.get("variant_budget", {}).get("max_variants"):
        notes.append(
            f"Variant budget capped selection at `{variant_matrix['variant_budget']['max_variants']}` candidates."
        )
    if variant_matrix.get("variant_budget", {}).get("max_short_cycle_runs"):
        notes.append(
            f"Short-cycle runs were capped at `{variant_matrix['variant_budget']['max_short_cycle_runs']}` candidates."
        )
    if metric_policy.get("primary_metric"):
        notes.append(
            f"Executed runs are ranked by `{metric_policy['primary_metric']}` with goal `{metric_policy['metric_goal']}`."
        )
    if executed_runs:
        notes.append(f"Executed `{len(executed_runs)}` candidate variants and fed their results back into `best_runs`.")
    return notes


def build_context(
    *,
    repo_path: Path,
    context_id: str,
    current_research: str,
    experiment_branch: str,
    durable_current_research: Dict[str, Any],
    workspace_info: Dict[str, Any],
    scan_data: Dict[str, Any],
    setup_plan: Dict[str, Any],
    analysis_data: Dict[str, Any],
    code_plan: Dict[str, Any],
    variant_matrix: Dict[str, Any],
    variant_spec: Dict[str, Any],
    executed_runs: List[Dict[str, Any]],
    planned_skill_chain: List[str],
    helper_stage_trace: List[Dict[str, Any]],
    include_analysis_pass: bool,
    include_setup_pass: bool,
) -> Dict[str, Any]:
    metric_policy = extract_metric_policy(variant_matrix, variant_spec)
    explore_context = {
        "context_id": context_id,
        "current_research": current_research,
        "experiment_branch": experiment_branch,
        "explicit_explore_authorization": True,
        "isolated_workspace": workspace_info.get("isolated_workspace", True),
        "workspace_mode": workspace_info.get("mode", "branch"),
        "workspace_root": workspace_info.get("workspace_root"),
    }
    return {
        "schema_version": "1.0",
        "context_id": context_id,
        "status": "completed" if executed_runs else "planned",
        "explore_context": explore_context,
        "current_research": current_research,
        "baseline_ref": current_research,
        "experiment_branch": experiment_branch,
        "isolated_workspace": explore_context["isolated_workspace"],
        "workspace_mode": explore_context["workspace_mode"],
        "workspace_root": explore_context["workspace_root"],
        "durable_current_research": durable_current_research,
        "source_repo_refs": code_plan.get("source_repo_refs")
        or [
            {
                "repo": repo_path.name,
                "ref": current_research,
                "note": "current_research anchor",
            }
        ],
        "raw_variant_count": variant_matrix.get("raw_variant_count", variant_matrix.get("variant_count", 0)),
        "variant_count": variant_matrix.get("variant_count", 0),
        "pruned_variant_count": variant_matrix.get("pruned_variant_count", 0),
        "variant_budget": variant_matrix.get("variant_budget", {"max_variants": 0, "max_short_cycle_runs": 0}),
        "selection_policy": variant_matrix.get("selection_policy", {}),
        "metric_policy": metric_policy,
        "best_runs": executed_runs,
        "candidate_edit_targets": code_plan.get("candidate_edit_targets", []),
        "code_tracks": code_plan.get("proposed_code_tracks", []),
        "candidate_hypotheses": build_candidate_hypotheses(variant_spec, analysis_data, code_plan),
        "planned_skill_chain": planned_skill_chain,
        "helper_stage_trace": helper_stage_trace,
        "recommended_next_trials": build_recommended_next_trials(
            variant_matrix,
            metric_policy,
            setup_plan,
            analysis_data,
            code_plan,
            executed_runs,
        ),
        "trusted_promote_candidate": False,
        "explicit_explore_authorization": True,
        "changes_summary": build_changes_summary(
            context_id,
            current_research,
            experiment_branch,
            workspace_info,
            code_plan,
            executed_runs,
            planned_skill_chain,
            variant_matrix,
            metric_policy,
            include_analysis_pass,
            include_setup_pass,
        ),
        "execution_notes": build_execution_notes(
            workspace_info,
            scan_data,
            setup_plan,
            analysis_data,
            code_plan,
            variant_matrix,
            metric_policy,
            executed_runs,
        ),
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
    parser.add_argument(
        "--run-selected-variants",
        action="store_true",
        help="Execute a small number of exploratory variants through the trusted execution helpers.",
    )
    parser.add_argument("--max-executed-variants", type=int, default=1, help="Maximum number of exploratory variants to execute when execution is enabled.")
    parser.add_argument("--variant-timeout", type=int, default=60, help="Timeout in seconds for each executed exploratory variant.")
    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()
    base_dir = Path(__file__).resolve().parents[2]
    scan_script = base_dir / "repo-intake-and-plan" / "scripts" / "scan_repo.py"
    setup_script = base_dir / "env-and-assets-bootstrap" / "scripts" / "plan_setup.py"
    analysis_script = base_dir / "analyze-project" / "scripts" / "analyze_project.py"
    code_planner_script = base_dir / "explore-code" / "scripts" / "plan_code_changes.py"
    planner_script = base_dir / "explore-run" / "scripts" / "plan_variants.py"
    run_execute_script = base_dir / "minimal-run-and-audit" / "scripts" / "run_command.py"
    train_execute_script = base_dir / "run-train" / "scripts" / "run_training.py"
    writer_script = Path(__file__).resolve().parent / "write_outputs.py"

    durable_current_research = validate_current_research(repo_path, args.current_research)
    experiment_branch = choose_experiment_branch(args.current_research, args.experiment_branch)
    workspace_info = ensure_experiment_workspace(repo_path, experiment_branch)
    context_id = build_context_id(args.current_research, experiment_branch)

    helper_stage_trace = [
        build_stage_trace_entry(
            "validate-current-research",
            "research-explore/validate_current_research",
            f"Validated durable current research `{args.current_research}` as `{durable_current_research['kind']}`.",
        ),
        build_stage_trace_entry(
            "workspace",
            "research-explore/ensure_experiment_workspace",
            (
                f"{'Created' if workspace_info['created_branch'] else 'Validated'} isolated "
                f"{workspace_info['mode']} for branch `{experiment_branch}` at `{workspace_info['workspace_root']}`."
            ),
        ),
    ]
    workspace_repo_path = Path(workspace_info["workspace_root"]).resolve()

    scan_data = run_json(scan_script, ["--repo", str(workspace_repo_path), "--json"])
    helper_stage_trace.append(
        build_stage_trace_entry(
            "repo-scan",
            "repo-intake-and-plan/scripts/scan_repo.py",
            f"Scanned repository structure and README signals for `{repo_path.name}`.",
        )
    )

    setup_plan = run_json(setup_script, ["--repo", str(workspace_repo_path), "--json"]) if args.include_setup_pass else {}
    if args.include_setup_pass:
        helper_stage_trace.append(
            build_stage_trace_entry(
                "setup-plan",
                "env-and-assets-bootstrap/scripts/plan_setup.py",
                "Planned environment and asset setup for exploratory execution.",
            )
        )

    analysis_data = run_json(analysis_script, ["--repo", str(workspace_repo_path), "--json"]) if args.include_analysis_pass else {}
    if args.include_analysis_pass:
        helper_stage_trace.append(
            build_stage_trace_entry(
                "analysis-pass",
                "analyze-project/scripts/analyze_project.py",
                "Ran a conservative read-only analysis pass before wider exploratory edits.",
            )
        )

    code_plan_args = [
        "--repo",
        str(workspace_repo_path),
        "--current-research",
        args.current_research,
        "--experiment-branch",
        experiment_branch,
        "--json",
    ]
    if args.variant_spec_json:
        code_plan_args.extend(["--variant-spec-json", args.variant_spec_json])
    code_plan = run_json(code_planner_script, code_plan_args)
    helper_stage_trace.append(
        build_stage_trace_entry(
            "code-plan",
            "explore-code/scripts/plan_code_changes.py",
            f"Prepared {len(code_plan.get('candidate_edit_targets', []))} candidate edit targets.",
        )
    )

    variant_matrix, variant_spec = build_variant_matrix(planner_script, args.variant_spec_json, args.current_research)
    metric_policy = extract_metric_policy(variant_matrix, variant_spec)
    execution_kind = (
        infer_execution_kind(variant_matrix.get("base_command"), variant_spec)
        if variant_matrix.get("base_command")
        else None
    )
    helper_stage_trace.append(
        build_stage_trace_entry(
            "run-plan",
            "explore-run/scripts/plan_variants.py",
            (
                f"Prepared {variant_matrix.get('variant_count', 0)} exploratory run variants"
                f" after pruning {variant_matrix.get('pruned_variant_count', 0)} by budget."
            ),
        )
    )

    planned_skill_chain: List[str] = []
    if args.include_analysis_pass:
        planned_skill_chain.append("analyze-project")
    if args.include_setup_pass:
        planned_skill_chain.append("env-and-assets-bootstrap")
    planned_skill_chain.extend(["explore-code", "explore-run"])
    executed_runs: List[Dict[str, Any]] = []
    if args.run_selected_variants:
        if variant_matrix.get("base_command") and variant_matrix.get("variants"):
            planned_skill_chain.append("run-train" if execution_kind == "training" else "minimal-run-and-audit")
        executed_runs, execution_trace = execute_variant_candidates(
            train_execute_script=train_execute_script,
            run_execute_script=run_execute_script,
            repo_path=workspace_repo_path,
            variant_matrix=variant_matrix,
            variant_spec=variant_spec,
            current_research=args.current_research,
            timeout=args.variant_timeout,
            max_executed_variants=args.max_executed_variants,
        )
        helper_stage_trace.extend(execution_trace)

    output_dir = Path(args.output_dir).resolve()
    helper_stage_trace.append(
        build_stage_trace_entry(
            "bundle-write",
            "research-explore/scripts/write_outputs.py",
            f"Writing the exploratory output bundle into `{output_dir}`.",
        )
    )

    context = build_context(
        repo_path=repo_path,
        context_id=context_id,
        current_research=args.current_research,
        experiment_branch=experiment_branch,
        durable_current_research=durable_current_research,
        workspace_info=workspace_info,
        scan_data=scan_data,
        setup_plan=setup_plan,
        analysis_data=analysis_data,
        code_plan=code_plan,
        variant_matrix=variant_matrix,
        variant_spec=variant_spec,
        executed_runs=executed_runs,
        planned_skill_chain=planned_skill_chain,
        helper_stage_trace=helper_stage_trace,
        include_analysis_pass=args.include_analysis_pass,
        include_setup_pass=args.include_setup_pass,
    )

    write_bundle(writer_script, output_dir, context)

    payload = {
        "schema_version": "1.0",
        "context_id": context_id,
        "repo": str(repo_path),
        "current_research": args.current_research,
        "experiment_branch": experiment_branch,
        "workspace": workspace_info,
        "durable_current_research": durable_current_research,
        "planned_skill_chain": planned_skill_chain,
        "candidate_edit_targets": code_plan.get("candidate_edit_targets", []),
        "code_tracks": code_plan.get("proposed_code_tracks", []),
        "raw_variant_count": context["raw_variant_count"],
        "variant_count": context["variant_count"],
        "pruned_variant_count": context["pruned_variant_count"],
        "variant_budget": context["variant_budget"],
        "selection_policy": context["selection_policy"],
        "metric_policy": context["metric_policy"],
        "execution_kind": execution_kind,
        "candidate_hypotheses": context["candidate_hypotheses"],
        "recommended_next_trials": context["recommended_next_trials"],
        "executed_variant_count": len(executed_runs),
        "best_runs": executed_runs,
        "setup_commands": setup_plan.get("setup_commands", []),
        "setup_notes": setup_plan.get("setup_notes", []),
        "analysis_summary": analysis_data.get("summary_lines", []),
        "analysis_suspicious_patterns": analysis_data.get("suspicious_patterns", []),
        "invoked_stage_trace": helper_stage_trace,
        "base_command": variant_matrix.get("base_command"),
        "output_dir": str(output_dir),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
