#!/usr/bin/env python3
"""Regression checks for legacy variant-spec contracts without analyze-project."""

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
        "# Demo Legacy Repo\n\n"
        "## Training\n\n"
        "```bash\n"
        "python train.py --config configs/demo.yaml\n"
        "```\n",
        encoding="utf-8",
    )
    (root / "train.py").write_text("print('train stub')\n", encoding="utf-8")
    (root / "model.py").write_text("class DemoModel:\n    pass\n", encoding="utf-8")
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

    temp_root = Path(tempfile.mkdtemp(prefix="codex-legacy-no-analysis-", dir=repo_root))
    try:
        sample_repo = temp_root / "sample_repo"
        sample_repo.mkdir()
        write_repo(sample_repo)
        init_git_repo(sample_repo)

        spec = {
            "current_research": "legacy-no-analysis@abc1234",
            "base_command": "python train.py --config configs/demo.yaml",
            "variant_axes": {"adapter": ["none", "lora"]},
            "subset_sizes": [16],
            "short_run_steps": [5],
        }
        spec_path = temp_root / "variant-spec.json"
        spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")

        output_dir = temp_root / "explore_outputs"
        subprocess.run(
            [
                sys.executable,
                str(orchestrator),
                "--repo",
                str(sample_repo),
                "--current-research",
                "legacy-no-analysis@abc1234",
                "--output-dir",
                str(output_dir),
                "--variant-spec-json",
                str(spec_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        analysis_status = json.loads((temp_root / "analysis_outputs" / "status.json").read_text(encoding="utf-8"))
        missing_outputs = [
            key
            for key, rel in analysis_status["outputs"].items()
            if not (temp_root / rel).exists()
        ]
        if missing_outputs:
            raise AssertionError(f"legacy no-analysis status advertised missing analysis artifacts: {missing_outputs}")

        print("ok: True")
        print("checks: 1")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root, onerror=remove_readonly)


if __name__ == "__main__":
    raise SystemExit(main())
