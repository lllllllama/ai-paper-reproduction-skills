#!/usr/bin/env python3
"""Minimal orchestration for README-first reproduction scaffolding.

This script wires together the repository scan, README command extraction,
optional execution of the selected documented command, and standardized
output generation. It is intentionally conservative and lightweight.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def run_json(script: Path, args: List[str]) -> Dict[str, Any]:
    """Run a helper script and parse its JSON stdout."""
    command = [sys.executable, str(script), *args]
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def choose_goal(commands: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Choose the highest-priority documented command."""
    priority = ["inference", "evaluation", "training", "other"]
    for category in priority:
        for item in commands:
            if item.get("category") == category:
                return {
                    "selected_goal": category,
                    "goal_priority": category,
                    "documented_command": item.get("command", ""),
                    "command_source": item.get("source", "readme"),
                }

    return {
        "selected_goal": "repo-intake-only",
        "goal_priority": "other",
        "documented_command": "",
        "command_source": "none",
    }


def maybe_run_command(
    repo_path: Path,
    command: str,
    timeout: int,
) -> Dict[str, Any]:
    """Optionally execute the selected command in a conservative way."""
    if not command:
        return {
            "status": "not_run",
            "documented_command_status": "not_run",
            "execution_log": [],
            "main_blocker": "No documented command was extracted from README.",
        }

    try:
        result = subprocess.run(
            shlex.split(command, posix=False),
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return {
            "status": "blocked",
            "documented_command_status": "blocked",
            "execution_log": [f"Command failed before launch: {exc}"],
            "main_blocker": f"Executable not found for documented command: {exc}",
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "partial",
            "documented_command_status": "partial",
            "execution_log": [f"Command timed out after {timeout} seconds."],
            "main_blocker": f"Selected documented command did not finish within {timeout} seconds.",
        }

    combined = []
    if result.stdout.strip():
        combined.append("STDOUT:\n" + result.stdout.strip())
    if result.stderr.strip():
        combined.append("STDERR:\n" + result.stderr.strip())

    return_code = result.returncode
    if return_code == 0:
        status = "success"
        cmd_status = "success"
        blocker = "None."
    else:
        status = "partial"
        cmd_status = "partial"
        blocker = f"Selected documented command exited with code {return_code}."

    return {
        "status": status,
        "documented_command_status": cmd_status,
        "execution_log": combined,
        "main_blocker": blocker,
    }


def build_context(
    repo_path: Path,
    scan_data: Dict[str, Any],
    command_data: Dict[str, Any],
    run_data: Dict[str, Any],
    user_language: str,
    run_selected: bool,
) -> Dict[str, Any]:
    """Build a single context object for output generation."""
    chosen = choose_goal(command_data.get("commands", []))
    status = run_data["status"] if run_selected else "not_run"
    documented_status = (
        run_data["documented_command_status"]
        if run_selected
        else ("not_run" if not chosen["documented_command"] else "documented")
    )

    structure = scan_data.get("structure", {})
    notes = []
    notes.extend(scan_data.get("warnings", []))
    notes.extend(command_data.get("warnings", []))
    notes.extend(run_data.get("execution_log", []))

    result_summary = (
        f"Selected goal `{chosen['selected_goal']}` from README evidence."
        if chosen["documented_command"]
        else "No documented runnable command was extracted. Repo intake was completed."
    )

    if run_selected and status == "success":
        result_summary = "Selected documented command finished successfully."
    elif run_selected and status == "partial":
        result_summary = "Selected documented command started but did not complete cleanly."
    elif run_selected and status == "blocked":
        result_summary = "Selected documented command could not be launched."

    return {
        "schema_version": "1.0",
        "generated_at": scan_data.get("generated_at"),
        "user_language": user_language,
        "target_repo": str(repo_path.resolve()),
        "readme_first": True,
        "selected_goal": chosen["selected_goal"],
        "goal_priority": chosen["goal_priority"],
        "status": status,
        "documented_command_status": documented_status,
        "documented_command": chosen["documented_command"] or "None extracted",
        "result_summary": result_summary,
        "main_blocker": run_data.get("main_blocker", "No blocker recorded."),
        "next_action": "Prepare environment and assets, then retry the documented command."
        if status in {"partial", "blocked", "not_run"}
        else "Review outputs and continue with the next documented verification step.",
        "setup_commands": [
            "conda env create -f environment.yml",
            "conda activate <env-name>",
        ],
        "asset_commands": [
            "# Add README-documented dataset and checkpoint preparation commands here.",
        ],
        "run_commands": [chosen["documented_command"]] if chosen["documented_command"] else [],
        "verification_commands": [
            "# Add metric check, artifact check, or smoke verification command here.",
        ],
        "command_notes": [
            f"README path: {scan_data.get('readme_path') or 'not found'}",
            f"Detected top-level entries: {', '.join(structure.get('top_level', [])) or 'none'}",
        ],
        "timeline": [
            "Scanned repository structure and key metadata files.",
            "Extracted README code blocks and shell-like commands.",
            f"Selected `{chosen['selected_goal']}` as the smallest trustworthy target.",
            "Execution step was skipped." if not run_selected else "Attempted the selected documented command.",
        ],
        "assumptions": [
            "README remains the primary source of truth.",
            "Environment creation should prefer conda-style isolation.",
        ],
        "evidence": [
            f"Detected files: {', '.join(scan_data.get('detected_files', [])) or 'none'}",
            f"Command categories: {json.dumps(command_data.get('counts', {}), ensure_ascii=False)}",
        ],
        "blockers": [run_data.get("main_blocker", "None.")],
        "notes": notes,
        "patches_applied": False,
        "patch_branch": "",
        "verified_commits": [],
        "validation_summary": "",
        "patch_notes": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a minimal README-first reproduction orchestration.")
    parser.add_argument("--repo", required=True, help="Path to the target repository.")
    parser.add_argument(
        "--output-dir",
        default="repro_outputs",
        help="Directory to write the standardized outputs into.",
    )
    parser.add_argument(
        "--user-language",
        default="en",
        help="Language tag for human-readable reports.",
    )
    parser.add_argument(
        "--run-selected",
        action="store_true",
        help="Execute the first selected documented command.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Execution timeout in seconds for --run-selected.",
    )
    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()
    base_dir = Path(__file__).resolve().parents[2]
    scan_script = base_dir / "repo-intake-and-plan" / "scripts" / "scan_repo.py"
    extract_script = base_dir / "repo-intake-and-plan" / "scripts" / "extract_commands.py"
    write_script = base_dir / "minimal-run-and-audit" / "scripts" / "write_outputs.py"

    scan_data = run_json(scan_script, ["--repo", str(repo_path), "--json"])
    readme_path = scan_data.get("readme_path")
    command_data = {"commands": [], "counts": {}, "warnings": []}
    if readme_path:
        command_data = run_json(extract_script, ["--readme", readme_path, "--json"])

    chosen = choose_goal(command_data.get("commands", []))
    run_data = {
        "status": "not_run",
        "documented_command_status": "not_run",
        "execution_log": [],
        "main_blocker": "Execution was not requested.",
    }
    if args.run_selected:
        run_data = maybe_run_command(repo_path, chosen["documented_command"], args.timeout)

    context = build_context(
        repo_path=repo_path,
        scan_data=scan_data,
        command_data=command_data,
        run_data=run_data,
        user_language=args.user_language,
        run_selected=args.run_selected,
    )

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    context_path = output_dir / ".repro_context.json"
    context_path.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")

    subprocess.run(
        [
            sys.executable,
            str(write_script),
            "--context-json",
            str(context_path),
            "--output-dir",
            str(output_dir),
        ],
        check=True,
    )

    print(json.dumps(context, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
