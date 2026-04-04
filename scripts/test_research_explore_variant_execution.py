#!/usr/bin/env python3
"""Regression checks for ai-research-explore variant execution handoff."""

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
        "# Demo Research Repo\n\n"
        "## Training\n\n"
        "```bash\n"
        "python train.py --config \"configs/demo config.yaml\"\n"
        "```\n",
        encoding="utf-8",
    )
    (root / "train.py").write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "args = sys.argv[1:]\n"
        "config_path = args[args.index('--config') + 1]\n"
        "Path(config_path).read_text()\n"
        "Path('execution-cwd.txt').write_text(Path.cwd().as_posix(), encoding='utf-8')\n"
        "adapter = args[args.index('--adapter') + 1] if '--adapter' in args else 'none'\n"
        "steps = int(args[args.index('--max-steps') + 1]) if '--max-steps' in args else 1\n"
        "metric = 0.83 if adapter == 'lora' else 0.71\n"
        "loss = 0.42 if adapter == 'lora' else 0.18\n"
        "print(f'step: {steps}')\n"
        "print(f'val_acc: {metric}')\n"
        "print(f'val_loss: {loss}')\n"
        "print('saved checkpoints/best.pt')\n",
        encoding="utf-8",
    )
    (root / "model.py").write_text("class DemoModel:\n    pass\n", encoding="utf-8")
    (root / "environment.yml").write_text("name: demo-env\ndependencies:\n  - python=3.10\n", encoding="utf-8")
    (root / "configs").mkdir()
    (root / "configs" / "demo config.yaml").write_text("model: demo\n", encoding="utf-8")


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

    temp_root = Path(tempfile.mkdtemp(prefix="codex-ai-research-explore-exec-", dir=repo_root))
    try:
        sample_repo = temp_root / "sample_repo"
        sample_repo.mkdir()
        write_repo(sample_repo)
        init_git_repo(sample_repo)

        spec = {
            "current_research": "improved-branch@abc1234",
            "base_command": "python train.py --config \"configs/demo config.yaml\"",
            "variant_axes": {
                "adapter": ["none", "lora"],
            },
            "subset_sizes": [64],
            "short_run_steps": [5],
            "primary_metric": "val_loss",
            "metric_goal": "minimize",
        }
        spec_path = temp_root / "variant-spec.json"
        spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")

        output_dir = temp_root / "explore_outputs"
        result = subprocess.run(
            [
                sys.executable,
                str(orchestrator),
                "--repo",
                str(sample_repo),
                "--current-research",
                "improved-branch@abc1234",
                "--output-dir",
                str(output_dir),
                "--variant-spec-json",
                str(spec_path),
                "--run-selected-variants",
                "--max-executed-variants",
                "2",
                "--variant-timeout",
                "30",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(result.stdout)
        workspace_root = Path(payload["workspace"]["workspace_root"])
        if payload["executed_variant_count"] != 2:
            raise AssertionError("ai-research-explore did not execute the requested number of variants")
        if payload["workspace"]["mode"] != "worktree":
            raise AssertionError("ai-research-explore did not execute training variants in an isolated worktree")
        if workspace_root.resolve() == sample_repo.resolve():
            raise AssertionError("ai-research-explore reused the original checkout instead of an isolated worktree")
        if not (workspace_root / "execution-cwd.txt").exists():
            raise AssertionError("ai-research-explore did not run the training command inside the isolated worktree")
        if (sample_repo / "execution-cwd.txt").exists():
            raise AssertionError("ai-research-explore leaked training execution side effects into the original checkout")
        if len(payload["best_runs"]) != 2:
            raise AssertionError("ai-research-explore did not surface executed runs as best_runs")
        if payload["best_runs"][0]["id"] != "variant-001":
            raise AssertionError("ai-research-explore failed to apply metric-aware ranking for training variants")
        if payload["best_runs"][0]["best_metric"]["name"] != "val_acc":
            raise AssertionError("ai-research-explore lost best_metric metadata from run-train handoff")
        if payload["best_runs"][0]["ranking_metric_name"] != "val_loss":
            raise AssertionError("ai-research-explore did not record the explicit training ranking metric")
        if "changed_files" not in payload["best_runs"][0] or "new_files" not in payload["best_runs"][0] or "touched_paths" not in payload["best_runs"][0]:
            raise AssertionError("ai-research-explore training execution lost executor evidence fields")
        if not any("execution-cwd.txt" in item.get("new_files", []) for item in payload["best_runs"]):
            raise AssertionError("ai-research-explore training execution did not preserve new file evidence from run-train")
        if payload["selection_policy"]["factors"] != ["cost", "success_rate", "expected_gain"]:
            raise AssertionError("ai-research-explore lost the pre-execution selection policy")
        if payload["metric_policy"]["primary_metric"] != "val_loss":
            raise AssertionError("ai-research-explore lost the explicit training metric policy")
        if not any(entry["tool"] == "run-train/scripts/run_training.py" for entry in payload["invoked_stage_trace"]):
            raise AssertionError("ai-research-explore failed to record run-train handoff in the stage trace")

        status = json.loads((output_dir / "status.json").read_text(encoding="utf-8"))
        if status["status"] != "completed":
            raise AssertionError("ai-research-explore status did not advance after executing candidate variants")
        if len(status["best_runs"]) != 2:
            raise AssertionError("ai-research-explore status lost executed best_runs")
        if status["best_runs"][0]["id"] != "variant-001":
            raise AssertionError("ai-research-explore status lost metric-aware training ordering")
        if status["selection_policy"]["factors"] != ["cost", "success_rate", "expected_gain"]:
            raise AssertionError("ai-research-explore status lost selection policy")

        top_runs = (output_dir / "TOP_RUNS.md").read_text(encoding="utf-8")
        if "val_loss" not in top_runs:
            raise AssertionError("ai-research-explore top-runs summary lost training ranking policy")
        if "variant-001" not in top_runs:
            raise AssertionError("ai-research-explore top-runs summary lost executed variant ranking")

        print("ok: True")
        print("checks: 17")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root, onerror=remove_readonly)


if __name__ == "__main__":
    raise SystemExit(main())

