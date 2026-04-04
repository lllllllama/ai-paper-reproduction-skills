#!/usr/bin/env python3
"""Regression checks for campaign baseline-gate abandonment."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


def write_repo(root: Path) -> None:
    (root / "README.md").write_text("# Demo Repo\n", encoding="utf-8")
    (root / "eval.py").write_text("print('miou: 74.0')\n", encoding="utf-8")
    (root / "train.py").write_text("print('miou: 74.5')\n", encoding="utf-8")
    (root / "configs").mkdir()
    (root / "configs" / "demo.yaml").write_text("model: demo\n", encoding="utf-8")


def init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "codex@example.com"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Codex"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=root, check=True, capture_output=True, text=True)


def remove_readonly(func, path, _excinfo) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    orchestrator = repo_root / "skills" / "ai-research-explore" / "scripts" / "orchestrate_explore.py"

    temp_root = Path(tempfile.mkdtemp(prefix="codex-research-campaign-abandon-", dir=repo_root))
    try:
        sample_repo = temp_root / "sample_repo"
        sample_repo.mkdir()
        write_repo(sample_repo)
        init_git_repo(sample_repo)

        campaign = {
            "current_research": "seg-branch@abc1234",
            "task_family": "segmentation",
            "dataset": "DemoSeg",
            "benchmark": {"name": "DemoBench", "primary_metric": "miou", "metric_goal": "maximize"},
            "evaluation_source": {
                "command": "python eval.py",
                "path": "eval.py",
                "primary_metric": "miou",
                "metric_goal": "maximize",
            },
            "sota_reference": [
                {"name": "Provided SOTA", "metric": "miou", "value": 80.0}
            ],
            "candidate_ideas": [
                {
                    "id": "idea-lora-rank",
                    "summary": "Increase LoRA rank while keeping the decoder unchanged.",
                    "change_scope": "lora_rank",
                    "target_component": "segmentation_head",
                    "expected_upside": 0.85,
                    "implementation_risk": 0.2,
                    "eval_risk": 0.15,
                    "rollback_ease": 0.9,
                    "estimated_runtime_cost": 0.35,
                    "single_variable_fit": 0.95,
                }
            ],
            "variant_spec": {
                "current_research": "seg-branch@abc1234",
                "base_command": "python train.py",
                "variant_axes": {"lora_rank": ["8"]},
                "primary_metric": "miou",
                "metric_goal": "maximize",
            },
            "execution_policy": {
                "run_selected_variants": True,
                "max_executed_variants": 1,
                "variant_timeout": 30,
            },
        }
        campaign_path = temp_root / "research-campaign.json"
        campaign_path.write_text(json.dumps(campaign, indent=2, ensure_ascii=False), encoding="utf-8")

        output_dir = temp_root / "explore_outputs"
        result = subprocess.run(
            [
                sys.executable,
                str(orchestrator),
                "--repo",
                str(sample_repo),
                "--research-campaign-json",
                str(campaign_path),
                "--output-dir",
                str(output_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(result.stdout)
        if payload["baseline_gate"]["decision"] != "abandon":
            raise AssertionError("ai-research-explore did not abandon a far-from-SOTA baseline")
        if payload["executed_variant_count"] != 0:
            raise AssertionError("ai-research-explore should not execute campaign variants after baseline abandonment")
        if payload["short_run_gate"]["status"] != "not-run":
            raise AssertionError("ai-research-explore should keep short-run gate in not-run state after abandonment")

        print("ok: True")
        print("checks: 3")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root, onerror=remove_readonly)


if __name__ == "__main__":
    raise SystemExit(main())

