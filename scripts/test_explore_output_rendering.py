#!/usr/bin/env python3
"""Regression checks for exploratory output bundles."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"Missing `{needle}` in {label}")


def write_context(path: Path, mode: str) -> None:
    context = {
        "schema_version": "1.0",
        "status": "planned" if mode in {"code", "research"} else "completed",
        "current_research": "main@abc1234",
        "experiment_branch": "exp/lora-demo",
        "isolated_workspace": True,
        "source_repo_refs": [
            {"repo": "org/source-repo", "ref": "deadbeef", "note": "adapter block source"}
        ],
        "variant_count": 3,
        "best_runs": [
            {"id": "variant-001", "metric": "0.812", "summary": "LoRA rank 8 on subset A"}
        ],
        "recommended_next_trials": [
            "Promote the best exploratory branch into a supervised rerun if metrics remain stable."
        ],
        "trusted_promote_candidate": False,
        "explicit_explore_authorization": True,
        "changes_summary": [
            "Added an isolated exploratory LoRA adapter path.",
            "Kept the trusted baseline untouched.",
        ],
        "execution_notes": ["Used a short-cycle 200-step run on a small subset."],
        "notes": ["Exploratory result only; not a trusted reproduction claim."],
    }
    path.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    code_writer = repo_root / "skills" / "explore-code" / "scripts" / "write_outputs.py"
    run_writer = repo_root / "skills" / "explore-run" / "scripts" / "write_outputs.py"
    research_writer = repo_root / "skills" / "research-explore" / "scripts" / "write_outputs.py"

    temp_root = Path(tempfile.mkdtemp(prefix="codex-explore-render-", dir=repo_root))
    try:
        for mode, writer in [("code", code_writer), ("run", run_writer), ("research", research_writer)]:
            context_path = temp_root / f"{mode}.json"
            output_dir = temp_root / mode / "explore_outputs"
            output_dir.parent.mkdir(parents=True, exist_ok=True)
            write_context(context_path, mode)

            subprocess.run(
                [sys.executable, str(writer), "--context-json", str(context_path), "--output-dir", str(output_dir)],
                check=True,
                capture_output=True,
                text=True,
            )

            changeset = (output_dir / "CHANGESET.md").read_text(encoding="utf-8")
            top_runs = (output_dir / "TOP_RUNS.md").read_text(encoding="utf-8")
            status = json.loads((output_dir / "status.json").read_text(encoding="utf-8"))

            assert_contains(changeset, "# Explore Changeset", f"{mode}/CHANGESET.md")
            assert_contains(changeset, "exp/lora-demo", f"{mode}/CHANGESET.md")
            assert_contains(top_runs, "# Top Runs", f"{mode}/TOP_RUNS.md")
            assert_contains(top_runs, "variant-001", f"{mode}/TOP_RUNS.md")

            if status["experiment_branch"] != "exp/lora-demo":
                raise AssertionError("explore status lost experiment_branch")
            if status["current_research"] != "main@abc1234":
                raise AssertionError("explore status lost current_research")
            if status["baseline_ref"] != "main@abc1234":
                raise AssertionError("explore status lost compatibility baseline_ref")
            if status["explicit_explore_authorization"] is not True:
                raise AssertionError("explore status lost explicit authorization flag")
            if status["variant_count"] != 3:
                raise AssertionError("explore status lost variant_count")

        print("ok: True")
        print("checks: 15")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())
