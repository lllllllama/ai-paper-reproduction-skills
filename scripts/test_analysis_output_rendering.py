#!/usr/bin/env python3
"""Regression checks for analyze-project outputs."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def write_repo(root: Path) -> None:
    (root / "README.md").write_text("# Demo\n", encoding="utf-8")
    (root / "train.py").write_text("import torch\n\ndef train():\n    pass\n", encoding="utf-8")
    (root / "model.py").write_text(
        "import torch\n"
        "import torch.nn.functional as F\n"
        "def forward(x):\n"
        "    x = F.relu(x)\n"
        "    x = torch.sigmoid(x)\n"
        "    return torch.sigmoid(x)\n",
        encoding="utf-8",
    )
    (root / "configs").mkdir()
    (root / "configs" / "demo.yaml").write_text("model: demo\n", encoding="utf-8")
    (root / "analysis_outputs").mkdir()
    (root / "analysis_outputs" / "eval_shadow.py").write_text("print('generated eval output')\n", encoding="utf-8")
    (root / "explore_outputs").mkdir()
    (root / "explore_outputs" / "metrics_dump.json").write_text("{}", encoding="utf-8")
    (root / "train_outputs").mkdir()
    (root / "train_outputs" / "model_snapshot.py").write_text("print('generated train output')\n", encoding="utf-8")
    (root / "debug_outputs").mkdir()
    (root / "debug_outputs" / "notes.txt").write_text("generated debug output\n", encoding="utf-8")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"Missing `{needle}` in {label}")


def assert_no_generated_outputs(values: list[str], label: str) -> None:
    generated_parts = ("analysis_outputs/", "explore_outputs/", "train_outputs/", "debug_outputs/")
    for value in values:
        if any(part in value for part in generated_parts):
            raise AssertionError(f"Generated output path leaked into {label}: {value}")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    analyzer = repo_root / "skills" / "analyze-project" / "scripts" / "analyze_project.py"

    temp_root = Path(tempfile.mkdtemp(prefix="codex-analysis-render-", dir=repo_root))
    try:
        sample_repo = temp_root / "sample_repo"
        sample_repo.mkdir()
        write_repo(sample_repo)
        output_dir = temp_root / "analysis_outputs"

        subprocess.run(
            [sys.executable, str(analyzer), "--repo", str(sample_repo), "--output-dir", str(output_dir)],
            check=True,
            capture_output=True,
            text=True,
        )

        summary = (output_dir / "SUMMARY.md").read_text(encoding="utf-8")
        risks = (output_dir / "RISKS.md").read_text(encoding="utf-8")
        research_map = (output_dir / "RESEARCH_MAP.md").read_text(encoding="utf-8")
        change_map = (output_dir / "CHANGE_MAP.md").read_text(encoding="utf-8")
        eval_contract = (output_dir / "EVAL_CONTRACT.md").read_text(encoding="utf-8")
        status = json.loads((output_dir / "status.json").read_text(encoding="utf-8"))

        assert_contains(summary, "# Project Analysis Summary", "SUMMARY.md")
        assert_contains(summary, "Train entry candidates", "SUMMARY.md")
        assert_contains(risks, "# Suspicious Patterns", "RISKS.md")
        assert_contains(risks, "sigmoid", "RISKS.md")
        assert_contains(research_map, "# Research Map", "RESEARCH_MAP.md")
        assert_contains(change_map, "# Change Map", "CHANGE_MAP.md")
        assert_contains(eval_contract, "# Eval Contract", "EVAL_CONTRACT.md")
        if "analysis_outputs/" in research_map or "explore_outputs/" in research_map:
            raise AssertionError("RESEARCH_MAP.md should not include generated output directories")

        if status["status"] != "analyzed":
            raise AssertionError("analysis status.json lost expected status")
        if "train.py" not in " ".join(status["entrypoints"]["train"]):
            raise AssertionError("analysis status.json lost expected train candidate")
        if "research_map" not in status["outputs"]:
            raise AssertionError("analysis status.json lost research_map output reference")
        assert_no_generated_outputs(status["entrypoints"]["train"], "status.entrypoints.train")
        assert_no_generated_outputs(status["task_relevant_files"], "status.task_relevant_files")
        assert_no_generated_outputs(status["research_map"]["task_relevant_files"], "status.research_map.task_relevant_files")
        if "idea_seeds" in status or "implementation_fidelity" in status:
            raise AssertionError("analyze-project status should not be polluted with ai-research-explore-only fields")

        print("ok: True")
        print("checks: 15")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())

