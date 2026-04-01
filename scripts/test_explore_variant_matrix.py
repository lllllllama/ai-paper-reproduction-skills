#!/usr/bin/env python3
"""Regression checks for exploratory variant matrix generation."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    planner = repo_root / "skills" / "explore-run" / "scripts" / "plan_variants.py"

    temp_root = Path(tempfile.mkdtemp(prefix="codex-explore-matrix-", dir=repo_root))
    try:
        spec = {
            "baseline_ref": "main@abc1234",
            "base_command": "python train.py --config configs/demo.yaml",
            "variant_axes": {
                "adapter": ["none", "lora"],
                "lr": ["1e-4", "5e-5"]
            },
            "subset_sizes": [128],
            "short_run_steps": [100, 200]
        }
        spec_path = temp_root / "spec.json"
        out_path = temp_root / "matrix.json"
        spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")

        subprocess.run(
            [sys.executable, str(planner), "--spec-json", str(spec_path), "--output-json", str(out_path)],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(out_path.read_text(encoding="utf-8"))
        if payload["variant_count"] != 8:
            raise AssertionError("unexpected variant_count in exploratory matrix")
        if payload["variants"][0]["subset_size"] != 128:
            raise AssertionError("subset size was not preserved")
        if payload["variants"][0]["short_run_steps"] not in {100, 200}:
            raise AssertionError("short-run step was not preserved")
        if sorted(payload["variants"][0]["axes"]) != ["adapter", "lr"]:
            raise AssertionError("variant axes were not preserved")

        print("ok: True")
        print("checks: 4")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())
