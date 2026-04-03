#!/usr/bin/env python3
"""Regression checks for legacy variant-spec output contracts."""

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
        "python train.py --config configs/demo.yaml\n"
        "```\n",
        encoding="utf-8",
    )
    (root / "train.py").write_text(
        "import argparse\n"
        "from model import DemoModel\n"
        "\n"
        "def main():\n"
        "    parser = argparse.ArgumentParser()\n"
        "    parser.add_argument('--config')\n"
        "    parser.parse_args()\n"
        "    DemoModel()\n"
        "    print('train stub')\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    main()\n",
        encoding="utf-8",
    )
    (root / "model.py").write_text(
        "class DemoModel:\n"
        "    def __init__(self):\n"
        "        self.name = 'demo'\n"
        "\n"
        "    def forward(self, x):\n"
        "        return x\n",
        encoding="utf-8",
    )
    (root / "environment.yml").write_text("name: demo-env\ndependencies:\n  - python=3.10\n", encoding="utf-8")
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

    temp_root = Path(tempfile.mkdtemp(prefix="codex-legacy-contract-", dir=repo_root))
    try:
        sample_repo = temp_root / "sample_repo"
        sample_repo.mkdir()
        write_repo(sample_repo)
        init_git_repo(sample_repo)

        spec = {
            "current_research": "legacy-branch@abc1234",
            "base_command": "python train.py --config configs/demo.yaml",
            "variant_axes": {
                "adapter": ["none", "lora"],
                "lr": ["1e-4", "5e-5"],
            },
            "subset_sizes": [64],
            "short_run_steps": [20],
            "max_variants": 2,
            "max_short_cycle_runs": 1,
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
                "legacy-branch@abc1234",
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
        status = json.loads((output_dir / "status.json").read_text(encoding="utf-8"))
        analysis_status_path = temp_root / "analysis_outputs" / "status.json"
        analysis_status = json.loads(analysis_status_path.read_text(encoding="utf-8"))

        if payload["campaign"]["mode"] != "legacy":
            raise AssertionError("research-explore lost legacy mode under variant-spec orchestration")
        if payload["selected_source_record"] != status["selected_source_record"]:
            raise AssertionError("legacy variant-spec payload and status diverged on selected_source_record")
        if status["selected_source_record"] != status["experiment_manifest"]["selected_source_record"]:
            raise AssertionError("legacy variant-spec status and manifest diverged on selected_source_record")
        if not payload["sources_index_path"] or not Path(payload["sources_index_path"]).exists():
            raise AssertionError("legacy variant-spec run did not emit a valid sources index")
        if "static_smoke" not in status or "runtime_smoke" not in status:
            raise AssertionError("legacy variant-spec status lost split smoke sections")

        for rel in payload["analysis_artifacts"].values():
            if not Path(rel).exists():
                raise AssertionError(f"legacy variant-spec analysis artifact path does not exist: {rel}")
        for rel in analysis_status["outputs"].values():
            if not (temp_root / rel).exists():
                raise AssertionError(f"legacy variant-spec analysis status advertised a missing file: {rel}")
        for rel in status["outputs"].values():
            if not (temp_root / rel).exists():
                raise AssertionError(f"legacy variant-spec status advertised a missing file: {rel}")

        print("ok: True")
        print("checks: 10")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root, onerror=remove_readonly)


if __name__ == "__main__":
    raise SystemExit(main())
