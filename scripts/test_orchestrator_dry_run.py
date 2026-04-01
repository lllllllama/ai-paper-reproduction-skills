#!/usr/bin/env python3
"""Regression checks for orchestrator dry-run planning."""

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
    (root / "configs").mkdir()
    (root / "configs" / "demo.yaml").write_text("model: demo\n", encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    orchestrator = repo_root / "skills" / "ai-paper-reproduction" / "scripts" / "orchestrate_repro.py"

    temp_root = Path(tempfile.mkdtemp(prefix="codex-orchestrator-dry-run-", dir=repo_root))
    try:
        sample_repo = temp_root / "sample_repo"
        sample_repo.mkdir()
        write_repo(sample_repo)
        output_dir = temp_root / "repro_outputs"

        result = subprocess.run(
            [
                sys.executable,
                str(orchestrator),
                "--repo",
                str(sample_repo),
                "--output-dir",
                str(output_dir),
                "--include-analysis-pass",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(result.stdout)
        expected_chain = [
            "repo-intake-and-plan",
            "env-and-assets-bootstrap",
            "analyze-project",
            "run-train",
        ]

        if payload["selected_goal"] != "training":
            raise AssertionError("orchestrator failed to select training goal for the dry-run repo")
        if payload["execution_skill"] != "run-train":
            raise AssertionError("orchestrator failed to switch execution_skill to run-train")
        if payload["planned_skill_chain"] != expected_chain:
            raise AssertionError("orchestrator failed to emit the expected planned skill chain")
        if "Planned skill chain" not in "\n".join(payload["command_notes"]):
            raise AssertionError("orchestrator command notes lost the planned chain trace")
        for rel in ["SUMMARY.md", "COMMANDS.md", "LOG.md", "status.json"]:
            if not (output_dir / rel).exists():
                raise AssertionError(f"orchestrator dry-run failed to emit {rel}")

        print("ok: True")
        print("checks: 5")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())
