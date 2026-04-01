#!/usr/bin/env python3
"""Regression checks for safe-debug outputs."""

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


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    debugger = repo_root / "skills" / "safe-debug" / "scripts" / "safe_debug.py"

    temp_root = Path(tempfile.mkdtemp(prefix="codex-debug-render-", dir=repo_root))
    try:
        output_dir = temp_root / "debug_outputs"
        error_text = "Traceback (most recent call last):\nRuntimeError: CUDA out of memory"

        subprocess.run(
            [sys.executable, str(debugger), "--error-text", error_text, "--output-dir", str(output_dir)],
            check=True,
            capture_output=True,
            text=True,
        )

        diagnosis = (output_dir / "DIAGNOSIS.md").read_text(encoding="utf-8")
        patch_plan = (output_dir / "PATCH_PLAN.md").read_text(encoding="utf-8")
        status = json.loads((output_dir / "status.json").read_text(encoding="utf-8"))

        assert_contains(diagnosis, "# Debug Diagnosis", "DIAGNOSIS.md")
        assert_contains(diagnosis, "cuda_oom", "DIAGNOSIS.md")
        assert_contains(patch_plan, "# Patch Plan", "PATCH_PLAN.md")
        assert_contains(patch_plan, "Do not modify repository code until the researcher approves", "PATCH_PLAN.md")

        if status["status"] != "diagnosed":
            raise AssertionError("safe-debug status.json lost expected status")
        if status["category"] != "cuda_oom":
            raise AssertionError("safe-debug status.json lost expected category")
        if status["patch_authorized"] is not False:
            raise AssertionError("safe-debug must default to patch_authorized false")

        print("ok: True")
        print("checks: 7")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())
