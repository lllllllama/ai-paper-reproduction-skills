#!/usr/bin/env python3
"""Regression checks for campaign-centric research-explore flow."""

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
    (root / "README.md").write_text(
        "# Demo Segmentation Repo\n\n"
        "## Training\n\n"
        "```bash\n"
        "python train.py --config configs/demo.yaml\n"
        "```\n\n"
        "## Evaluation\n\n"
        "```bash\n"
        "python eval.py --config configs/demo.yaml\n"
        "```\n",
        encoding="utf-8",
    )
    (root / "train.py").write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "args = sys.argv[1:]\n"
        "config = args[args.index('--config') + 1]\n"
        "Path(config).read_text()\n"
        "rank = args[args.index('--lora-rank') + 1] if '--lora-rank' in args else '4'\n"
        "miou = 80.4 if rank == '8' else 79.8\n"
        "val_loss = 0.18 if rank == '8' else 0.31\n"
        "print(f'miou: {miou}')\n"
        "print(f'val_loss: {val_loss}')\n"
        "print('saved checkpoints/best.pt')\n",
        encoding="utf-8",
    )
    (root / "eval.py").write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "args = sys.argv[1:]\n"
        "config = args[args.index('--config') + 1]\n"
        "Path(config).read_text()\n"
        "print('miou: 79.2')\n",
        encoding="utf-8",
    )
    (root / "segmentation_head.py").write_text("class SegHead:\n    pass\n", encoding="utf-8")
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
    orchestrator = repo_root / "skills" / "research-explore" / "scripts" / "orchestrate_explore.py"

    temp_root = Path(tempfile.mkdtemp(prefix="codex-research-campaign-", dir=repo_root))
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
                "artifacts": ["metrics.json"],
            },
            "sota_reference": [
                {"name": "Provided SOTA", "metric": "miou", "value": 80.0, "source": "demo-paper"}
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
                },
                {
                    "id": "idea-aux-loss",
                    "summary": "Add an auxiliary loss branch.",
                    "change_scope": "aux_loss",
                    "target_component": "trainer",
                    "expected_upside": 0.6,
                    "implementation_risk": 0.4,
                    "eval_risk": 0.35,
                    "rollback_ease": 0.6,
                    "estimated_runtime_cost": 0.5,
                    "single_variable_fit": 0.7,
                },
            ],
            "compute_budget": {"max_runtime_hours": 2},
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
                "variant_axes": {"lora_rank": ["4", "8"]},
                "subset_sizes": [32],
                "short_run_steps": [3],
                "max_variants": 2,
                "max_short_cycle_runs": 2,
                "primary_metric": "val_loss",
                "metric_goal": "minimize",
            },
            "execution_policy": {
                "run_selected_variants": True,
                "max_executed_variants": 2,
                "variant_timeout": 1800,
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
        if payload["campaign"]["mode"] != "campaign":
            raise AssertionError("research-explore did not switch into campaign mode")
        if payload["baseline_gate"]["decision"] != "proceed":
            raise AssertionError("research-explore did not proceed after a near-SOTA baseline")
        if payload["selected_idea"]["id"] != "idea-lora-rank":
            raise AssertionError("research-explore selected the wrong top-ranked idea")
        if payload["human_checkpoint_state"] != "not-required":
            raise AssertionError("research-explore requested a checkpoint unexpectedly")
        if payload["metric_policy"]["primary_metric"] != "val_loss":
            raise AssertionError("research-explore did not preserve the run-ranking metric policy")
        if payload["campaign"]["execution_policy"]["max_executed_variants"] != 2:
            raise AssertionError("research-explore overwrote campaign max_executed_variants with CLI defaults")
        if payload["campaign"]["execution_policy"]["variant_timeout"] != 1800:
            raise AssertionError("research-explore overwrote campaign variant_timeout with CLI defaults")
        if payload["executed_variant_count"] != 2:
            raise AssertionError("research-explore did not execute the configured number of campaign variants")
        if payload["sota_claim_state"] != "candidate-exceeds-provided-sota":
            raise AssertionError("research-explore did not surface the provided-SOTA overtake state")
        if payload["short_run_gate"]["status"] != "passed":
            raise AssertionError("research-explore did not pass the short-run gate")
        if payload["lookup_record_count"] <= 0:
            raise AssertionError("research-explore did not emit lookup records")
        if not payload["minimal_patch_plan"]:
            raise AssertionError("research-explore did not emit a minimal patch plan")
        if payload["resource_plan"]["short_run_feasibility"] != "proceed":
            raise AssertionError("research-explore did not emit the resource feasibility summary")
        if payload["smoke_report"]["status"] != "passed":
            raise AssertionError("research-explore did not emit the smoke report")

        for rel in ["IDEA_GATE.md", "EXPERIMENT_PLAN.md", "EXPERIMENT_MANIFEST.md", "EXPERIMENT_LEDGER.md", "TRANSPLANT_SMOKE_REPORT.md", "status.json"]:
            if not (output_dir / rel).exists():
                raise AssertionError(f"research-explore campaign flow failed to emit {rel}")

        analysis_dir = temp_root / "analysis_outputs"
        for rel in ["RESEARCH_MAP.md", "CHANGE_MAP.md", "EVAL_CONTRACT.md", "SOURCE_INVENTORY.md", "SOURCE_SUPPORT.json", "IMPROVEMENT_BANK.md", "IDEA_CARDS.json", "IDEA_EVALUATION.md", "IDEA_SCORES.json", "MODULE_CANDIDATES.md", "INTERFACE_DIFF.md", "RESOURCE_PLAN.md", "status.json"]:
            if not (analysis_dir / rel).exists():
                raise AssertionError(f"research-explore campaign flow failed to emit analysis_outputs/{rel}")
        idea_scores = json.loads((analysis_dir / "IDEA_SCORES.json").read_text(encoding="utf-8"))
        if not idea_scores or idea_scores[0]["id"] != payload["selected_idea"]["id"]:
            raise AssertionError("research-explore selected_idea diverged from IDEA_SCORES.json[0]")
        sources_dir = temp_root / "sources"
        for rel in ["index.json", "SUMMARY.md"]:
            if not (sources_dir / rel).exists():
                raise AssertionError(f"research-explore campaign flow failed to emit sources/{rel}")
        if not (sources_dir / "records").exists():
            raise AssertionError("research-explore campaign flow failed to emit sources/records")

        status = json.loads((output_dir / "status.json").read_text(encoding="utf-8"))
        if status["campaign"]["task_family"] != "segmentation":
            raise AssertionError("research-explore status lost campaign task_family")
        if status["baseline_gate"]["decision"] != "proceed":
            raise AssertionError("research-explore status lost baseline gate decision")
        if status["selected_idea"]["id"] != "idea-lora-rank":
            raise AssertionError("research-explore status lost selected idea")
        if status["sota_claim_state"] != "candidate-exceeds-provided-sota":
            raise AssertionError("research-explore status lost SOTA claim state")
        if status["metric_policy"]["primary_metric"] != "val_loss":
            raise AssertionError("research-explore status lost the run-ranking metric policy")
        if status["resource_plan"]["short_run_feasibility"] != "proceed":
            raise AssertionError("research-explore status lost resource feasibility")
        if status["smoke_report"]["status"] != "passed":
            raise AssertionError("research-explore status lost smoke report")
        if not status["lookup_records"]:
            raise AssertionError("research-explore status lost lookup records")
        if not status["source_inventory_path"] or not status["source_support_path"]:
            raise AssertionError("research-explore status lost source inventory/support artifact paths")
        if status["source_record_count"] <= 0:
            raise AssertionError("research-explore status lost source record count")

        print("ok: True")
        print("checks: 36")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root, onerror=remove_readonly)


if __name__ == "__main__":
    raise SystemExit(main())
