#!/usr/bin/env python3
"""Regression checks for run-train outputs."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List


def build_context(case: str) -> Dict[str, object]:
    base = {
        "schema_version": "1.0",
        "generated_at": "2026-04-01T00:00:00Z",
        "user_language": "en",
        "target_repo": "D:/demo/research-repo",
        "selected_goal": "training",
        "documented_command_status": "partial",
        "documented_command": "python train.py --config configs/demo.yaml",
        "documented_command_kind": "train",
        "documented_command_source": "readme_code_block",
        "documented_command_section": "Training",
        "setup_commands": [{"label": "adapted", "command": "conda env create -f environment.yml"}],
        "asset_commands": [{"label": "documented", "command": "python scripts/prepare_data.py"}],
        "run_commands": [{"label": "documented", "command": "python train.py --config configs/demo.yaml"}],
        "verification_commands": [{"label": "inferred", "command": "python tools/check_latest_ckpt.py"}],
        "command_notes": ["Training command came from the README training section."],
        "timeline": ["Prepared the environment.", "Started the selected training command."],
        "assumptions": ["Dataset path remains consistent with the README."],
        "evidence": ["Observed checkpoint directory creation."],
        "blockers": [],
        "human_decisions_required": ["Confirm whether to extend beyond the current verification window."],
        "next_safe_action": "Review the captured training status before increasing the run scope.",
        "artifact_provenance": [
            {"artifact": "train_command", "source": "README.md", "kind": "repo_file"},
            {"artifact": "train_outputs", "source": "train_outputs/", "kind": "generated"},
        ],
        "notes": [],
    }

    if case == "startup":
        return {
            **base,
            "status": "partial",
            "run_mode": "startup_verification",
            "resume_from": None,
            "dataset": "demo-train",
            "checkpoint_source": "none",
            "max_steps": 50,
            "completed_steps": 12,
            "best_metric": None,
            "best_checkpoint": None,
            "stop_reason": "startup_verified",
            "result_summary": "The selected training command started successfully and produced early training evidence.",
            "main_blocker": "The run stopped after the planned startup verification window.",
            "next_action": "Decide whether to continue the run or keep this as startup-only evidence.",
        }
    if case == "blocked":
        return {
            **base,
            "status": "blocked",
            "run_mode": "full_kickoff",
            "resume_from": None,
            "dataset": "demo-train",
            "checkpoint_source": "baseline.ckpt",
            "max_steps": 1000,
            "completed_steps": 0,
            "best_metric": None,
            "best_checkpoint": None,
            "stop_reason": "dataset_missing",
            "blockers": ["Dataset path was missing at launch time."],
            "result_summary": "The training command could not start because the dataset path was unresolved.",
            "main_blocker": "Dataset path was missing at launch time.",
            "next_action": "Fix the dataset path assumption and retry the same documented command.",
        }
    if case == "resume":
        return {
            **base,
            "status": "partial",
            "run_mode": "resume",
            "resume_from": "checkpoints/last.pt",
            "dataset": "demo-train",
            "checkpoint_source": "checkpoints/last.pt",
            "max_steps": 10000,
            "completed_steps": 6400,
            "best_metric": {"name": "val_acc", "value": 0.84},
            "best_checkpoint": "checkpoints/best.pt",
            "stop_reason": "manual_pause",
            "result_summary": "The resumed training run progressed and produced an updated best checkpoint.",
            "main_blocker": "The run was paused manually after the scheduled verification window.",
            "next_action": "Review the latest metrics and decide whether to continue from the resumed checkpoint.",
        }
    raise ValueError(f"Unknown case: {case}")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"Missing `{needle}` in {label}")


def run_case(writer: Path, temp_root: Path, case: str) -> List[str]:
    case_dir = temp_root / case
    case_dir.mkdir()
    context_path = case_dir / "context.json"
    output_dir = case_dir / "train_outputs"
    context = build_context(case)
    context_path.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")

    subprocess.run(
        [sys.executable, str(writer), "--context-json", str(context_path), "--output-dir", str(output_dir)],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = (output_dir / "SUMMARY.md").read_text(encoding="utf-8")
    commands = (output_dir / "COMMANDS.md").read_text(encoding="utf-8")
    log = (output_dir / "LOG.md").read_text(encoding="utf-8")
    status = json.loads((output_dir / "status.json").read_text(encoding="utf-8"))

    assert_contains(summary, "# Training Run Summary", f"{case}/SUMMARY.md")
    assert_contains(commands, "# Training Commands", f"{case}/COMMANDS.md")
    assert_contains(log, "# Training Log", f"{case}/LOG.md")
    assert_contains(log, "## Human review checkpoints", f"{case}/LOG.md")

    if (output_dir / "PATCHES.md").exists():
        raise AssertionError("run-train should not emit PATCHES.md")

    checks = [
        status["run_mode"] == context["run_mode"],
        status["status"] == context["status"],
        status["dataset"] == context["dataset"],
        status["checkpoint_source"] == context["checkpoint_source"],
        status["completed_steps"] == context["completed_steps"],
        status["max_steps"] == context["max_steps"],
        status["stop_reason"] == context["stop_reason"],
        status["next_safe_action"] == context["next_safe_action"],
    ]
    if not all(checks):
        raise AssertionError(f"run-train status.json lost expected fields for case `{case}`")

    if case == "resume":
        if status["resume_from"] != "checkpoints/last.pt":
            raise AssertionError("resume metadata was not preserved")
        if status["best_checkpoint"] != "checkpoints/best.pt":
            raise AssertionError("best checkpoint metadata was not preserved")
        if status["best_metric"]["name"] != "val_acc":
            raise AssertionError("best metric metadata was not preserved")

    return [summary, commands, log]


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    writer = repo_root / "skills" / "run-train" / "scripts" / "write_outputs.py"

    temp_root = Path(tempfile.mkdtemp(prefix="codex-train-render-", dir=repo_root))
    try:
        for case in ["startup", "blocked", "resume"]:
            run_case(writer, temp_root, case)

        print("ok: True")
        print("checks: 15")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())
