#!/usr/bin/env python3
"""Regression checks for README command extraction and selection heuristics."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


def run_extract(script: Path, readme_text: str) -> Dict[str, Any]:
    temp_path = script.parent / ".tmp_readme_selection.md"
    temp_path.write_text(readme_text, encoding="utf-8")
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--readme", str(temp_path), "--json"],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def command_score(command: Dict[str, Any]) -> int:
    text = str(command.get("command", "")).lower()
    kind = command.get("kind", "run")
    section = str(command.get("section") or "").lower()
    score = {"run": 40, "smoke": 30, "asset": 10, "setup": 0}.get(kind, 0)
    if any(token in text for token in ["python ", "python3 ", "./", "whisper "]):
        score += 8
    if any(token in text for token in ["txt2img", "img2img", "amg.py", "transcribe", "infer", "eval"]):
        score += 8
    if any(token in section for token in ["usage", "demo", "example", "inference", "evaluation", "text-to-image", "image-to-image"]):
        score += 6
    if any(token in section for token in ["install", "installation", "setup", "environment"]):
        score -= 6
    if "<" in text and ">" in text:
        score -= 10
    if text.startswith(("pip install", "conda install", "conda env create", "conda activate", "git clone", "cd ")):
        score -= 12
    return score


def choose_goal(commands: List[Dict[str, Any]]) -> str:
    priority = ["inference", "evaluation", "training", "other"]
    for category in priority:
        candidates = [item for item in commands if item.get("category") == category]
        if candidates:
            best = max(candidates, key=command_score)
            return str(best.get("command", ""))
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run README extraction and selection regression tests.")
    parser.add_argument(
        "--cases",
        default="tests/readme_selection_cases.json",
        help="Path to README selection cases JSON.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    extract_script = repo_root / "skills" / "repo-intake-and-plan" / "scripts" / "extract_commands.py"
    payload = json.loads((repo_root / args.cases).read_text(encoding="utf-8"))

    failures: List[str] = []
    for case in payload["cases"]:
        extracted = run_extract(extract_script, case["readme"])
        selected = choose_goal(extracted["commands"])
        if selected != case["expected_command"]:
            failures.append(f"{case['id']}: expected `{case['expected_command']}`, got `{selected}`")

    print(f"ok: {not failures}")
    print(f"cases: {len(payload['cases'])}")
    print(f"failures: {len(failures)}")
    for failure in failures:
        print(f"FAIL: {failure}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
