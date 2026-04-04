#!/usr/bin/env python3
"""Regression checks for canonical source-mapping artifact consistency."""

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
    (root / "README.md").write_text("# Demo Consistency Repo\n", encoding="utf-8")
    (root / "train.py").write_text("print('train stub')\n", encoding="utf-8")
    (root / "eval.py").write_text("print('miou: 79.2')\n", encoding="utf-8")
    (root / "segmentation_head.py").write_text(
        "class SegHead:\n"
        "    def __init__(self):\n"
        "        self.rank = 4\n",
        encoding="utf-8",
    )
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

    temp_root = Path(tempfile.mkdtemp(prefix="codex-artifact-consistency-", dir=repo_root))
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
                "command": "python eval.py --config configs/demo.yaml",
                "path": "eval.py",
                "primary_metric": "miou",
                "metric_goal": "maximize",
            },
            "sota_reference": [{"name": "Provided SOTA", "metric": "miou", "value": 80.0}],
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
            "research_lookup": {
                "seed_sources": [
                    {
                        "kind": "repo",
                        "title": "Segmentation head transplant",
                        "query": "segmentation_head transplant",
                        "url": "https://github.com/openai/gym",
                        "repo": "openai/gym",
                        "file": "gym/core.py",
                        "symbol": "Env",
                    }
                ]
            },
            "variant_spec": {
                "current_research": "seg-branch@abc1234",
                "base_command": "python train.py --config configs/demo.yaml",
                "axis_flag_map": {"lora_rank": "--lora-rank"},
                "variant_axes": {"lora_rank": ["8"]},
                "subset_sizes": [16],
                "short_run_steps": [1],
                "max_variants": 1,
                "max_short_cycle_runs": 1,
                "primary_metric": "miou",
                "metric_goal": "maximize",
            },
            "execution_policy": {
                "run_selected_variants": False,
                "max_executed_variants": 1,
                "variant_timeout": 60,
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
        explore_status = json.loads((output_dir / "status.json").read_text(encoding="utf-8"))
        analysis_status = json.loads((temp_root / "analysis_outputs" / "status.json").read_text(encoding="utf-8"))
        manifest = explore_status["experiment_manifest"]
        selected_source_record = payload["selected_source_record"]
        atomic_map = payload["atomic_idea_map"]
        fidelity_summary = payload["fidelity_summary"]

        if not selected_source_record:
            raise AssertionError("artifact consistency run did not produce a canonical selected_source_record")
        if selected_source_record != explore_status["selected_source_record"]:
            raise AssertionError("payload and explore status diverged on selected_source_record")
        if selected_source_record != analysis_status["selected_source_record"]:
            raise AssertionError("payload and analysis status diverged on selected_source_record")
        if selected_source_record != manifest["selected_source_record"]:
            raise AssertionError("payload and manifest diverged on selected_source_record")
        if payload["minimal_patch_plan"] != explore_status["minimal_patch_plan"]:
            raise AssertionError("payload and explore status diverged on minimal_patch_plan")
        if payload["minimal_patch_plan"] != analysis_status["minimal_patch_plan"]:
            raise AssertionError("payload and analysis status diverged on minimal_patch_plan")
        if payload["minimal_patch_plan"] != manifest["minimal_patch_plan"]:
            raise AssertionError("payload and manifest diverged on minimal_patch_plan")
        if payload["target_location_map"] != explore_status["target_location_map"]:
            raise AssertionError("payload and explore status diverged on target_location_map")
        if payload["target_location_map"] != manifest["target_location_map"]:
            raise AssertionError("payload and manifest diverged on target_location_map")
        if atomic_map != explore_status["atomic_idea_map"]:
            raise AssertionError("payload and explore status diverged on atomic_idea_map")
        if atomic_map != analysis_status["atomic_idea_map"]:
            raise AssertionError("payload and analysis status diverged on atomic_idea_map")
        if fidelity_summary != explore_status["fidelity_summary"]:
            raise AssertionError("payload and explore status diverged on fidelity_summary")
        if fidelity_summary != analysis_status["fidelity_summary"]:
            raise AssertionError("payload and analysis status diverged on fidelity_summary")
        if fidelity_summary != manifest["implementation_fidelity_summary"]:
            raise AssertionError("payload and manifest diverged on implementation_fidelity_summary")

        module_candidate = explore_status["module_candidates"][0]
        for key in ("source_repo", "source_file", "source_symbol"):
            if module_candidate[key] != selected_source_record[key]:
                raise AssertionError(f"module candidate diverged from canonical source record on {key}")

        manifest_md = (output_dir / "EXPERIMENT_MANIFEST.md").read_text(encoding="utf-8")
        module_candidates_md = (temp_root / "analysis_outputs" / "MODULE_CANDIDATES.md").read_text(encoding="utf-8")
        for value in (
            selected_source_record["source_repo"],
            selected_source_record["source_file"],
            selected_source_record["source_symbol"],
        ):
            if value not in manifest_md:
                raise AssertionError("manifest markdown lost canonical source triple details")
            if value not in module_candidates_md:
                raise AssertionError("module candidates markdown lost canonical source triple details")
        if "Atomic Idea Map" not in (temp_root / "analysis_outputs" / "ATOMIC_IDEA_MAP.md").read_text(encoding="utf-8"):
            raise AssertionError("atomic idea map markdown was not rendered")
        fidelity_md = (temp_root / "analysis_outputs" / "IMPLEMENTATION_FIDELITY.md").read_text(encoding="utf-8")
        if "Implementation Fidelity" not in fidelity_md:
            raise AssertionError("implementation fidelity markdown was not rendered")
        for key in fidelity_summary.get("verification_levels", {}):
            if key not in fidelity_md:
                raise AssertionError("implementation fidelity markdown diverged from fidelity summary verification levels")

        print("ok: True")
        print("checks: 18")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root, onerror=remove_readonly)


if __name__ == "__main__":
    raise SystemExit(main())

