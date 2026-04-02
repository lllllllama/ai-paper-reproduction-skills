#!/usr/bin/env python3
"""Regression checks for research-explore non-training variant execution handoff."""

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
        "# Demo Eval Repo\n\n"
        "## Evaluation\n\n"
        "```bash\n"
        "python eval.py --config \"configs/demo config.yaml\"\n"
        "```\n",
        encoding="utf-8",
    )
    (root / "eval.py").write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "args = sys.argv[1:]\n"
        "config_path = args[args.index('--config') + 1]\n"
        "Path(config_path).read_text()\n"
        "adapter = args[args.index('--adapter') + 1] if '--adapter' in args else 'none'\n"
        "metric = 0.92 if adapter == 'tuned' else 0.74\n"
        "latency = 18 if adapter == 'tuned' else 7\n"
        "print(f'latency: {latency}')\n"
        "print(f'acc: {metric}')\n",
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
    orchestrator = repo_root / "skills" / "research-explore" / "scripts" / "orchestrate_explore.py"

    temp_root = Path(tempfile.mkdtemp(prefix="codex-research-explore-nontrain-", dir=repo_root))
    try:
        sample_repo = temp_root / "sample_repo"
        sample_repo.mkdir()
        write_repo(sample_repo)
        init_git_repo(sample_repo)

        spec = {
            "current_research": "eval-branch@abc1234",
            "execution_kind": "verify",
            "base_command": "python eval.py --config \"configs/demo config.yaml\"",
            "variant_axes": {
                "adapter": ["none", "tuned"],
            },
            "primary_metric": "latency",
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
                "eval-branch@abc1234",
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
        if payload["executed_variant_count"] != 2:
            raise AssertionError("research-explore did not execute the requested non-training variants")
        if payload["best_runs"][0]["id"] != "variant-001":
            raise AssertionError("research-explore failed to apply metric-aware ranking for non-training variants")
        if payload["best_runs"][0]["best_metric"]["name"] != "acc":
            raise AssertionError("research-explore lost non-training metric metadata")
        if payload["best_runs"][0]["ranking_metric_name"] != "latency":
            raise AssertionError("research-explore did not record the explicit non-training ranking metric")
        if payload["selection_policy"]["factors"] != ["cost", "success_rate", "expected_gain"]:
            raise AssertionError("research-explore lost the pre-execution selection policy")
        if payload["metric_policy"]["primary_metric"] != "latency":
            raise AssertionError("research-explore lost the explicit non-training metric policy")
        if not any(entry["tool"] == "minimal-run-and-audit/scripts/run_command.py" for entry in payload["invoked_stage_trace"]):
            raise AssertionError("research-explore failed to record minimal-run handoff in the stage trace")

        status = json.loads((output_dir / "status.json").read_text(encoding="utf-8"))
        if status["status"] != "completed":
            raise AssertionError("research-explore status did not advance after non-training execution")
        if status["best_runs"][0]["id"] != "variant-001":
            raise AssertionError("research-explore status lost metric-aware non-training ordering")
        if status["selection_policy"]["factors"] != ["cost", "success_rate", "expected_gain"]:
            raise AssertionError("research-explore status lost selection policy")

        top_runs = (output_dir / "TOP_RUNS.md").read_text(encoding="utf-8")
        if "latency" not in top_runs:
            raise AssertionError("research-explore top-runs summary lost non-training ranking policy")

        print("ok: True")
        print("checks: 11")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root, onerror=remove_readonly)


if __name__ == "__main__":
    raise SystemExit(main())
