#!/usr/bin/env python3
"""Regression checks for exploratory output bundles."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"Missing `{needle}` in {label}")


def write_context(path: Path, mode: str) -> None:
    context = {
        "schema_version": "1.0",
        "context_id": "research-explore-demo",
        "status": "planned" if mode in {"code", "research"} else "completed",
        "explore_context": {
            "context_id": "research-explore-demo",
            "current_research": "main@abc1234",
            "experiment_branch": "exp/lora-demo",
            "explicit_explore_authorization": True,
            "isolated_workspace": True,
            "workspace_mode": "branch",
            "workspace_root": "D:/demo/repo",
        },
        "current_research": "main@abc1234",
        "experiment_branch": "exp/lora-demo",
        "isolated_workspace": True,
        "source_repo_refs": [
            {"repo": "org/source-repo", "ref": "deadbeef", "note": "adapter block source"}
        ],
        "variant_count": 3,
        "raw_variant_count": 5,
        "pruned_variant_count": 2,
        "variant_budget": {
            "max_variants": 3,
            "max_short_cycle_runs": 1,
        },
        "selection_policy": {
            "factors": ["cost", "success_rate", "expected_gain"],
            "weights": {
                "cost": 0.25,
                "success_rate": 0.35,
                "expected_gain": 0.4,
            },
        },
        "metric_policy": {
            "primary_metric": "val_loss",
            "metric_goal": "minimize",
        },
        "best_runs": [
            {
                "id": "variant-001",
                "metric": 0.812,
                "metric_name": "val_loss",
                "ranking_metric_name": "val_loss",
                "summary": "LoRA rank 8 on subset A",
            }
        ],
        "candidate_edit_targets": ["model.py", "configs/demo.yaml"],
        "code_tracks": ["Review adapter and head touchpoints before widening edits."],
        "helper_stage_trace": [
            {
                "stage": "workspace",
                "tool": "research-explore/ensure_experiment_workspace",
                "status": "completed",
                "summary": "Created isolated experiment branch `exp/lora-demo`.",
            }
        ],
        "recommended_next_trials": [
            "Promote the best exploratory branch into a supervised rerun if metrics remain stable."
        ],
        "trusted_promote_candidate": False,
        "explicit_explore_authorization": True,
        "campaign": {
            "mode": "campaign" if mode == "research" else "legacy",
            "task_family": "segmentation",
        },
        "eval_contract": {
            "task_family": "segmentation",
            "dataset": "DemoSet",
            "benchmark": "DemoBench",
            "evaluation_command": "python eval.py --config configs/demo.yaml",
            "primary_metric": "val_loss",
            "metric_goal": "minimize",
        },
        "baseline_gate": {
            "decision": "proceed",
            "metric_name": "val_loss",
            "metric_value": 0.9,
        },
        "idea_gate": {
            "decision": "selected",
            "ranked_ideas": [
                {"id": "idea-001", "idea_score": 0.77, "summary": "Tune the adapter rank."}
            ],
        },
        "selected_idea": {
            "id": "idea-001",
            "summary": "Tune the adapter rank.",
            "target_component": "adapter",
            "change_scope": "rank",
            "source_reference": ["paper:abc12345"],
        },
        "experiment_manifest": {
            "parent_baseline": "main@abc1234",
            "idea_id": "idea-001",
            "hypothesis": "Higher rank improves the exploratory validation metric.",
            "changed_files": ["model.py", "configs/demo.yaml"],
            "eval_contract_ref": "analysis_outputs/EVAL_CONTRACT.md",
            "primary_metric": "val_loss",
            "promotion_rule": "manual-review",
            "supporting_changes": ["config plumbing"],
            "selected_source_reference": ["paper:abc12345"],
            "target_location_map": [
                {"file": "model.py", "target_symbol": "AdapterBlock.__init__", "role": "code"}
            ],
            "minimal_patch_plan": [
                {"change_type": "import-glue", "target_files": ["model.py"]}
            ],
            "smoke_validation_plan": [
                {"name": "syntax-parse", "reason": "Keep Python parseable."}
            ],
            "feasibility_summary": {
                "short_run_feasibility": "proceed",
                "full_run_feasibility": "borderline",
            },
        },
        "experiment_ledger": {
            "baseline": {
                "metric_name": "val_loss",
                "metric_value": 0.9,
                "runtime_seconds": 7.0,
            },
            "candidate_runs": [
                {
                    "id": "variant-001",
                    "phase": "short-run",
                    "baseline_metric_diff": 0.088,
                    "runtime_seconds": 12.0,
                    "stop_reason": "short_run_verified",
                    "rollback_target": "exp/lora-demo",
                }
            ],
        },
        "short_run_gate": {
            "status": "passed",
            "reason": "Short-run gate passed with variant-001.",
        },
        "analysis_artifacts": {
            "analysis_status": "analysis_outputs/status.json",
            "source_inventory": "analysis_outputs/SOURCE_INVENTORY.md",
            "source_support": "analysis_outputs/SOURCE_SUPPORT.json",
            "improvement_bank": "analysis_outputs/IMPROVEMENT_BANK.md",
            "idea_cards": "analysis_outputs/IDEA_CARDS.json",
            "idea_evaluation": "analysis_outputs/IDEA_EVALUATION.md",
            "idea_scores": "analysis_outputs/IDEA_SCORES.json",
            "module_candidates": "analysis_outputs/MODULE_CANDIDATES.md",
            "interface_diff": "analysis_outputs/INTERFACE_DIFF.md",
            "resource_plan": "analysis_outputs/RESOURCE_PLAN.md",
        },
        "sources_dir": "D:/demo/sources",
        "sources_records_dir": "D:/demo/sources/records",
        "sources_index_path": "D:/demo/sources/index.json",
        "source_inventory_path": "D:/demo/analysis_outputs/SOURCE_INVENTORY.md",
        "source_support_path": "D:/demo/analysis_outputs/SOURCE_SUPPORT.json",
        "source_record_count": 1,
        "source_records_by_evidence_class": ["external_provider"],
        "lookup_records": [
            {
                "source_id": "paper:abc12345",
                "source_type": "paper",
                "title": "Adapter Paper",
                "artifact_path": "sources/records/paper__adapter__abc12345.json",
                "provider_type": "arxiv",
                "evidence_class": "external_provider",
            }
        ],
        "idea_cards": [
            {"id": "idea-001", "summary": "Tune the adapter rank."}
        ],
        "improvement_bank": [
            {"id": "idea-001", "summary": "Tune the adapter rank."}
        ],
        "target_location_map": [
            {"file": "model.py", "target_symbol": "AdapterBlock.__init__", "role": "code"}
        ],
        "supporting_changes": ["config plumbing"],
        "patch_surface_summary": {"estimated_patch_surface": "small", "target_count": 2},
        "minimal_patch_plan": [
            {"change_type": "import-glue", "target_files": ["model.py"]}
        ],
        "smoke_validation_plan": [
            {"name": "syntax-parse", "reason": "Keep Python parseable."}
        ],
        "module_candidates": [
            {"target_file": "model.py", "source_repo": "org/source-repo"}
        ],
        "interface_diff": {
            "constructor_surface": ["AdapterBlock.__init__"],
            "forward_surface": ["AdapterBlock.forward"],
        },
        "resource_plan": {
            "short_run_feasibility": "proceed",
            "full_run_feasibility": "borderline",
        },
        "resource_detection": {
            "cpu": {"logical_cores": 8},
            "gpu": {"available_backends": ["CUDA"]},
        },
        "resource_recommendations": {
            "parallel_strategy": "high-parallelism",
        },
        "static_smoke": {
            "status": "passed",
            "checks": [
                {"name": "syntax-parse", "status": "passed", "passed": ["model.py"], "blockers": []}
            ],
            "blockers": [],
        },
        "runtime_smoke": {
            "status": "planned",
            "checks": [
                {"name": "short-run-command", "status": "planned", "passed": [], "blockers": ["not-executed-yet"]}
            ],
            "blockers": [],
        },
        "smoke_report": {
            "status": "planned",
            "static_smoke": {
                "status": "passed",
                "checks": [
                    {"name": "syntax-parse", "status": "passed", "passed": ["model.py"], "blockers": []}
                ],
                "blockers": [],
            },
            "runtime_smoke": {
                "status": "planned",
                "checks": [
                    {"name": "short-run-command", "status": "planned", "passed": [], "blockers": ["not-executed-yet"]}
                ],
                "blockers": [],
            },
            "blockers": [],
        },
        "human_checkpoint_state": "not-required",
        "sota_claim_state": "candidate-exceeds-provided-sota",
        "changes_summary": [
            "Added an isolated exploratory LoRA adapter path.",
            "Kept the trusted baseline untouched.",
        ],
        "execution_notes": ["Used a short-cycle 200-step run on a small subset."],
        "notes": ["Exploratory result only; not a trusted reproduction claim."],
    }
    path.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    code_writer = repo_root / "skills" / "explore-code" / "scripts" / "write_outputs.py"
    run_writer = repo_root / "skills" / "explore-run" / "scripts" / "write_outputs.py"
    research_writer = repo_root / "skills" / "research-explore" / "scripts" / "write_outputs.py"

    temp_root = Path(tempfile.mkdtemp(prefix="codex-explore-render-", dir=repo_root))
    try:
        for mode, writer in [("code", code_writer), ("run", run_writer), ("research", research_writer)]:
            context_path = temp_root / f"{mode}.json"
            output_dir = temp_root / mode / "explore_outputs"
            output_dir.parent.mkdir(parents=True, exist_ok=True)
            write_context(context_path, mode)

            subprocess.run(
                [sys.executable, str(writer), "--context-json", str(context_path), "--output-dir", str(output_dir)],
                check=True,
                capture_output=True,
                text=True,
            )

            changeset = (output_dir / "CHANGESET.md").read_text(encoding="utf-8")
            top_runs = (output_dir / "TOP_RUNS.md").read_text(encoding="utf-8")
            status = json.loads((output_dir / "status.json").read_text(encoding="utf-8"))
            if mode == "research":
                for rel in ["IDEA_GATE.md", "EXPERIMENT_PLAN.md", "EXPERIMENT_MANIFEST.md", "EXPERIMENT_LEDGER.md", "TRANSPLANT_SMOKE_REPORT.md"]:
                    if not (output_dir / rel).exists():
                        raise AssertionError(f"Missing `{rel}` for research output rendering")
                manifest = (output_dir / "EXPERIMENT_MANIFEST.md").read_text(encoding="utf-8")
                smoke = (output_dir / "TRANSPLANT_SMOKE_REPORT.md").read_text(encoding="utf-8")
                assert_contains(manifest, "paper:abc12345", "research/EXPERIMENT_MANIFEST.md")
                assert_contains(smoke, "syntax-parse", "research/TRANSPLANT_SMOKE_REPORT.md")
                assert_contains(smoke, "Runtime Smoke", "research/TRANSPLANT_SMOKE_REPORT.md")

            assert_contains(changeset, "# Explore Changeset", f"{mode}/CHANGESET.md")
            assert_contains(changeset, "exp/lora-demo", f"{mode}/CHANGESET.md")
            assert_contains(top_runs, "# Top Runs", f"{mode}/TOP_RUNS.md")
            assert_contains(top_runs, "variant-001", f"{mode}/TOP_RUNS.md")
            assert_contains(top_runs, "val_loss", f"{mode}/TOP_RUNS.md")
            assert_contains(top_runs, "cost, success_rate, expected_gain", f"{mode}/TOP_RUNS.md")

            if status["experiment_branch"] != "exp/lora-demo":
                raise AssertionError("explore status lost experiment_branch")
            if status["current_research"] != "main@abc1234":
                raise AssertionError("explore status lost current_research")
            if status["baseline_ref"] != "main@abc1234":
                raise AssertionError("explore status lost compatibility baseline_ref")
            if status["explore_context"]["experiment_branch"] != "exp/lora-demo":
                raise AssertionError("explore status lost canonical explore_context")
            if status["explicit_explore_authorization"] is not True:
                raise AssertionError("explore status lost explicit authorization flag")
            if status["variant_count"] != 3:
                raise AssertionError("explore status lost variant_count")
            if status["raw_variant_count"] != 5:
                raise AssertionError("explore status lost raw_variant_count")
            if status["pruned_variant_count"] != 2:
                raise AssertionError("explore status lost pruned_variant_count")
            if status["metric_policy"]["primary_metric"] != "val_loss":
                raise AssertionError("explore status lost metric_policy")
            if status["variant_budget"]["max_variants"] != 3:
                raise AssertionError("explore status lost variant_budget")
            if status["selection_policy"]["factors"] != ["cost", "success_rate", "expected_gain"]:
                raise AssertionError("explore status lost selection_policy")
            if not status["helper_stage_trace"]:
                raise AssertionError("explore status lost helper stage trace")
            if mode == "research" and status["sota_claim_state"] != "candidate-exceeds-provided-sota":
                raise AssertionError("research explore status lost sota_claim_state")
            if mode == "research" and status["outputs"]["experiment_manifest"] != "explore_outputs/EXPERIMENT_MANIFEST.md":
                raise AssertionError("research explore status lost experiment_manifest output")
            if mode == "research" and status["resource_plan"]["short_run_feasibility"] != "proceed":
                raise AssertionError("research explore status lost resource plan")
            if mode == "research" and status["smoke_report"]["status"] != "planned":
                raise AssertionError("research explore status lost smoke report")
            if mode == "research" and status["static_smoke"]["status"] != "passed":
                raise AssertionError("research explore status lost static smoke")
            if mode == "research" and status["runtime_smoke"]["status"] != "planned":
                raise AssertionError("research explore status lost runtime smoke")
            if mode == "research" and status["sources_index_path"] != "D:/demo/sources/index.json":
                raise AssertionError("research explore status lost sources index path")
            if mode == "research" and status["source_inventory_path"] != "D:/demo/analysis_outputs/SOURCE_INVENTORY.md":
                raise AssertionError("research explore status lost source inventory path")
            if mode == "research" and status["source_record_count"] != 1:
                raise AssertionError("research explore status lost source record count")

        print("ok: True")
        print("checks: 40")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())
