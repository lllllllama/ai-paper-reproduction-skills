#!/usr/bin/env python3
"""Regression checks for analyze-project structural hints schema."""

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
    (root / "README.md").write_text("# Demo Analyze Repo\n", encoding="utf-8")
    (root / "model.py").write_text(
        "class AdapterModel:\n"
        "    def __init__(self, channels=32):\n"
        "        self.channels = channels\n"
        "\n"
        "    def forward(self, x):\n"
        "        return x\n",
        encoding="utf-8",
    )
    (root / "train.py").write_text(
        "import argparse\n"
        "from model import AdapterModel\n"
        "\n"
        "def main():\n"
        "    parser = argparse.ArgumentParser()\n"
        "    parser.add_argument('--config')\n"
        "    args = parser.parse_args()\n"
        "    AdapterModel()\n"
        "    print(args.config)\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    main()\n",
        encoding="utf-8",
    )
    (root / "eval.py").write_text(
        "def evaluate():\n"
        "    print('miou: 0.9')\n",
        encoding="utf-8",
    )
    (root / "configs").mkdir()
    (root / "configs" / "demo.yaml").write_text("model: adapter\n", encoding="utf-8")


def remove_readonly(func, path, _excinfo) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    analyzer = repo_root / "skills" / "analyze-project" / "scripts" / "analyze_project.py"

    temp_root = Path(tempfile.mkdtemp(prefix="codex-analyze-hints-", dir=repo_root))
    try:
        sample_repo = temp_root / "sample_repo"
        sample_repo.mkdir()
        write_repo(sample_repo)

        context = {
            "current_research": "adapter-branch@abc1234",
            "task_family": "segmentation",
            "dataset": "DemoSeg",
            "benchmark": {"name": "DemoBench", "primary_metric": "miou", "metric_goal": "maximize"},
            "evaluation_source": {
                "command": "python eval.py --config configs/demo.yaml",
                "path": "eval.py",
                "primary_metric": "miou",
                "metric_goal": "maximize",
            },
        }
        context_path = temp_root / "analysis-context.json"
        context_path.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")

        output_dir = temp_root / "analysis_outputs"
        result = subprocess.run(
            [
                sys.executable,
                str(analyzer),
                "--repo",
                str(sample_repo),
                "--output-dir",
                str(output_dir),
                "--analysis-context-json",
                str(context_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(result.stdout)
        status = json.loads((output_dir / "status.json").read_text(encoding="utf-8"))

        expected_keys = {
            "symbol_hints",
            "constructor_candidates",
            "forward_candidates",
            "config_binding_hints",
            "module_files",
            "metric_files",
        }
        if expected_keys - payload.keys():
            raise AssertionError("analyze-project JSON payload lost structural-hints keys")
        if expected_keys - status.keys():
            raise AssertionError("analyze-project status lost structural-hints keys")
        if "model.py:AdapterModel" not in payload["symbol_hints"]:
            raise AssertionError("analyze-project did not capture the model class symbol hint")
        if "model.py:AdapterModel" not in payload["constructor_candidates"]:
            raise AssertionError("analyze-project did not capture the constructor candidate")
        if "model.py:AdapterModel.forward" not in payload["forward_candidates"]:
            raise AssertionError("analyze-project did not capture the forward candidate")
        if "model.py" not in payload["module_files"]:
            raise AssertionError("analyze-project did not surface model.py as a module file")
        if "eval.py" not in payload["metric_files"]:
            raise AssertionError("analyze-project did not surface eval.py as a metric file")
        if not any(item in {"train.py", "configs/demo.yaml"} for item in payload["config_binding_hints"]):
            raise AssertionError("analyze-project did not surface any config-binding hint")

        for rel in status["outputs"].values():
            if not (temp_root / rel).exists():
                raise AssertionError(f"analyze-project status advertised a missing output: {rel}")

        print("ok: True")
        print("checks: 10")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root, onerror=remove_readonly)


if __name__ == "__main__":
    raise SystemExit(main())
