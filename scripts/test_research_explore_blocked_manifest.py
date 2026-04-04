#!/usr/bin/env python3
"""Regression checks for blocked experiment manifests when no idea passes the gate."""

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
    (root / "eval.py").write_text("print('miou: 79.4')\n", encoding="utf-8")
    (root / "train.py").write_text("print('miou: 80.0')\n", encoding="utf-8")
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

    temp_root = Path(tempfile.mkdtemp(prefix="codex-research-blocked-manifest-", dir=repo_root))
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
            "sota_reference": [{"name": "Provided SOTA", "metric": "miou", "value": 80.0}],
            "candidate_ideas": [
                {
                    "id": "idea-bad",
                    "summary": "Rewrite everything.",
                    "change_scope": "broad_rewrite",
                    "target_component": "trainer",
                    "expected_upside": 0.9,
                    "implementation_risk": 0.9,
                    "eval_risk": 0.8,
                    "rollback_ease": 0.1,
                    "estimated_runtime_cost": 0.9,
                    "single_variable_fit": 0.2,
                }
            ],
            "idea_generation": {
                "allow_synthesized_seed_ideas": False,
                "max_generated_ideas": 0,
            },
            "variant_spec": {
                "current_research": "seg-branch@abc1234",
                "base_command": "python train.py",
                "variant_axes": {"adapter": ["a"]},
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
        manifest = payload["experiment_manifest"]
        if manifest["status"] != "blocked":
            raise AssertionError("ai-research-explore did not block the manifest when no idea passed")
        if "no-selected-idea" not in manifest["blockers"]:
            raise AssertionError("ai-research-explore lost the blocked-manifest reason")
        if payload["executed_variant_count"] != 0:
            raise AssertionError("ai-research-explore should not execute variants when the manifest is blocked")
        rendered = (output_dir / "EXPERIMENT_MANIFEST.md").read_text(encoding="utf-8")
        if "Status: `blocked`" not in rendered:
            raise AssertionError("rendered experiment manifest lost the blocked state")

        print("ok: True")
        print("checks: 4")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root, onerror=remove_readonly)


if __name__ == "__main__":
    raise SystemExit(main())

