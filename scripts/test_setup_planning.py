#!/usr/bin/env python3
"""Regression checks for conservative environment setup planning."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    planner = repo_root / "skills" / "env-and-assets-bootstrap" / "scripts" / "plan_setup.py"

    temp_root = Path(tempfile.mkdtemp(prefix="codex-setup-plan-", dir=repo_root))
    try:
        sample_repo = temp_root / "sample_repo"
        sample_repo.mkdir()
        (sample_repo / "environment.yml").write_text("name: demo-env\ndependencies:\n  - python=3.10\n", encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(planner), "--repo", str(sample_repo), "--json"],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)

        if payload["environment_file"] != "environment.yml":
            raise AssertionError("setup planner failed to detect environment.yml")
        if payload["environment_name"] != "demo-env":
            raise AssertionError("setup planner failed to detect the conda environment name")
        if payload["setup_commands"][0]["command"] != "conda env create -f environment.yml":
            raise AssertionError("setup planner failed to emit the expected conda create command")
        if payload["setup_commands"][1]["command"] != "conda activate demo-env":
            raise AssertionError("setup planner failed to emit the expected conda activate command")
        if payload["setup_commands"][0]["platforms"] != ["windows", "macos", "linux"]:
            raise AssertionError("setup planner lost the cross-platform tag for conda setup")

        requirements_repo = temp_root / "requirements_repo"
        requirements_repo.mkdir()
        (requirements_repo / "requirements.txt").write_text("numpy\n", encoding="utf-8")

        requirements_result = subprocess.run(
            [sys.executable, str(planner), "--repo", str(requirements_repo), "--json"],
            check=True,
            capture_output=True,
            text=True,
        )
        requirements_payload = json.loads(requirements_result.stdout)

        if requirements_payload["setup_commands"][0]["command"] != "python -m venv .venv":
            raise AssertionError("setup planner failed to emit the virtualenv bootstrap command")
        if requirements_payload["setup_commands"][1]["command"] != ".\\.venv\\Scripts\\Activate.ps1":
            raise AssertionError("setup planner failed to emit the Windows activation command")
        if requirements_payload["setup_commands"][1]["platforms"] != ["windows"]:
            raise AssertionError("setup planner failed to scope the Windows activation command")
        if requirements_payload["setup_commands"][2]["command"] != "source .venv/bin/activate":
            raise AssertionError("setup planner failed to emit the POSIX activation command")
        if requirements_payload["setup_commands"][2]["platforms"] != ["macos", "linux"]:
            raise AssertionError("setup planner failed to scope the POSIX activation command")

        print("ok: True")
        print("checks: 10")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())
