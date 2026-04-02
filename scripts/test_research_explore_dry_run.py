#!/usr/bin/env python3
"""Regression checks for research-explore orchestration dry runs."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def write_repo(root: Path) -> None:
    (root / "README.md").write_text(
        "# Demo Research Repo\n\n"
        "## Training\n\n"
        "```bash\n"
        "python train.py --config configs/demo.yaml\n"
        "```\n",
        encoding="utf-8",
    )
    (root / "train.py").write_text("print('train stub')\n", encoding="utf-8")
    (root / "model.py").write_text("class DemoModel:\n    pass\n", encoding="utf-8")
    (root / "environment.yml").write_text("name: demo-env\ndependencies:\n  - python=3.10\n", encoding="utf-8")
    (root / "configs").mkdir()
    (root / "configs" / "demo.yaml").write_text("model: demo\n", encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    orchestrator = repo_root / "skills" / "research-explore" / "scripts" / "orchestrate_explore.py"

    temp_root = Path(tempfile.mkdtemp(prefix="codex-research-explore-", dir=repo_root))
    try:
        sample_repo = temp_root / "sample_repo"
        sample_repo.mkdir()
        write_repo(sample_repo)

        spec = {
            "current_research": "improved-branch@abc1234",
            "base_command": "python train.py --config configs/demo.yaml",
            "variant_axes": {
                "adapter": ["none", "lora"],
                "lr": ["1e-4", "5e-5"],
            },
            "subset_sizes": [128],
            "short_run_steps": [100, 200],
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
                "--include-analysis-pass",
                "--include-setup-pass",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(result.stdout)
        expected_chain = [
            "analyze-project",
            "env-and-assets-bootstrap",
            "explore-code",
            "explore-run",
        ]

        if payload["current_research"] != "improved-branch@abc1234":
            raise AssertionError("research-explore lost current_research")
        if payload["planned_skill_chain"] != expected_chain:
            raise AssertionError("research-explore emitted the wrong planned skill chain")
        if payload["variant_count"] != 8:
            raise AssertionError("research-explore emitted the wrong variant_count")
        if payload["setup_commands"][0]["command"] != "conda env create -f environment.yml":
            raise AssertionError("research-explore failed to propagate setup commands")
        if payload["setup_commands"][0]["platforms"] != ["windows", "macos", "linux"]:
            raise AssertionError("research-explore lost setup command platform metadata")
        if not payload["recommended_next_trials"]:
            raise AssertionError("research-explore failed to recommend next trials")

        for rel in ["CHANGESET.md", "TOP_RUNS.md", "status.json"]:
            if not (output_dir / rel).exists():
                raise AssertionError(f"research-explore dry-run failed to emit {rel}")

        status = json.loads((output_dir / "status.json").read_text(encoding="utf-8"))
        if status["current_research"] != "improved-branch@abc1234":
            raise AssertionError("research-explore status lost current_research")
        if status["planned_skill_chain"] != expected_chain:
            raise AssertionError("research-explore status lost planned skill chain")

        print("ok: True")
        print("checks: 8")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())
