#!/usr/bin/env python3
"""Regression checks for transplant smoke report rendering."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    writer = repo_root / "skills" / "ai-research-explore" / "scripts" / "write_outputs.py"

    temp_root = Path(tempfile.mkdtemp(prefix="codex-smoke-report-", dir=repo_root))
    try:
        context = {
            "schema_version": "1.0",
            "context_id": "ai-research-explore-smoke",
            "status": "planned",
            "explore_context": {
                "context_id": "ai-research-explore-smoke",
                "current_research": "main@abc1234",
                "experiment_branch": "exp/smoke-demo",
                "explicit_explore_authorization": True,
                "isolated_workspace": True,
                "workspace_mode": "branch",
                "workspace_root": "D:/demo/repo",
            },
            "current_research": "main@abc1234",
            "experiment_branch": "exp/smoke-demo",
            "campaign": {"mode": "campaign"},
            "source_repo_refs": [],
            "metric_policy": {"primary_metric": "val_loss", "metric_goal": "minimize"},
            "baseline_gate": {"decision": "proceed"},
            "idea_gate": {"decision": "selected", "ranked_ideas": []},
            "selected_idea": {"id": "idea-001", "summary": "Shim adapter"},
            "experiment_manifest": {
                "idea_id": "idea-001",
                "hypothesis": "Test shim smoke path.",
                "target_location_map": [{"file": "model.py", "target_symbol": "Demo.forward", "role": "code"}],
                "minimal_patch_plan": [{"change_type": "import-glue", "target_files": ["model.py"]}],
                "smoke_validation_plan": [{"name": "syntax-parse", "reason": "Keep Python parseable."}],
                "feasibility_summary": {"short_run_feasibility": "blocked", "full_run_feasibility": "blocked"},
            },
            "experiment_ledger": {"baseline": {}, "candidate_runs": []},
            "short_run_gate": {"status": "failed", "reason": "blocked"},
            "resource_plan": {"short_run_feasibility": "blocked", "full_run_feasibility": "blocked"},
            "static_smoke": {
                "status": "failed",
                "checks": [
                    {"name": "config-path", "status": "failed", "passed": [], "blockers": ["configs/demo.yaml"]},
                ],
                "blockers": ["configs/demo.yaml"],
            },
            "runtime_smoke": {
                "status": "planned",
                "checks": [
                    {"name": "short-run-command", "status": "planned", "passed": [], "blockers": ["not-executed-yet"]},
                ],
                "blockers": [],
            },
            "smoke_report": {
                "status": "failed",
                "static_smoke": {
                    "status": "failed",
                    "checks": [
                        {"name": "config-path", "status": "failed", "passed": [], "blockers": ["configs/demo.yaml"]},
                    ],
                    "blockers": ["configs/demo.yaml"],
                },
                "runtime_smoke": {
                    "status": "planned",
                    "checks": [
                        {"name": "short-run-command", "status": "planned", "passed": [], "blockers": ["not-executed-yet"]},
                    ],
                    "blockers": [],
                },
                "blockers": ["configs/demo.yaml"],
            },
            "notes": ["Exploratory result only; not a trusted reproduction claim."],
        }
        context_path = temp_root / "context.json"
        context_path.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")
        output_dir = temp_root / "explore_outputs"

        subprocess.run(
            [sys.executable, str(writer), "--context-json", str(context_path), "--output-dir", str(output_dir)],
            check=True,
            capture_output=True,
            text=True,
        )

        report = (output_dir / "TRANSPLANT_SMOKE_REPORT.md").read_text(encoding="utf-8")
        status = json.loads((output_dir / "status.json").read_text(encoding="utf-8"))
        if "Candidate-only semantics" not in report:
            raise AssertionError("smoke report lost candidate-only wording")
        if "Static Smoke" not in report or "Runtime Smoke" not in report:
            raise AssertionError("smoke report did not split static and runtime smoke")
        if "configs/demo.yaml" not in report:
            raise AssertionError("smoke report lost blocker details")
        if status["outputs"]["transplant_smoke_report"] != "explore_outputs/TRANSPLANT_SMOKE_REPORT.md":
            raise AssertionError("status lost transplant smoke report output")
        if status["smoke_report"]["status"] != "failed":
            raise AssertionError("status lost failed smoke report state")
        if status["runtime_smoke"]["status"] != "planned":
            raise AssertionError("status lost runtime smoke state")

        print("ok: True")
        print("checks: 6")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())

