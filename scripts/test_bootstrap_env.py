#!/usr/bin/env python3
"""Regression checks for the cross-platform environment bootstrapper."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    bootstrapper = repo_root / "skills" / "env-and-assets-bootstrap" / "scripts" / "bootstrap_env.py"

    temp_root = Path(tempfile.mkdtemp(prefix="codex-bootstrap-env-", dir=repo_root))
    try:
        sample_repo = temp_root / "sample_repo"
        sample_repo.mkdir()
        (sample_repo / "requirements.txt").write_text("numpy\n", encoding="utf-8")

        env = dict(os.environ)
        env["PATH"] = ""

        result = subprocess.run(
            [sys.executable, str(bootstrapper), str(sample_repo), "demo-env", "--dry-run"],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        output = result.stdout

        if "Detected environment file: requirements.txt" not in output:
            raise AssertionError("bootstrapper failed to detect requirements.txt")
        if "-m venv" not in output:
            raise AssertionError("bootstrapper failed to fall back to virtualenv when conda is unavailable")
        if ".\\.venv\\Scripts\\Activate.ps1" not in output:
            raise AssertionError("bootstrapper failed to print the Windows activation hint")
        if "source .venv/bin/activate" not in output:
            raise AssertionError("bootstrapper failed to print the POSIX activation hint")

        print("ok: True")
        print("checks: 4")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())
