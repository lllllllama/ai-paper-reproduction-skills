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
            "current_research": "main@abc1234",
            "base_command": "python train.py --config configs/demo.yaml",
            "variant_axes": {
                "adapter": ["none", "lora"],
                "lr": ["1e-4", "5e-5"]
            },
            "subset_sizes": [128],
            "short_run_steps": [None, 100],
            "max_variants": 3,
            "max_short_cycle_runs": 1,
            "primary_metric": "val_loss",
            "metric_goal": "minimize",
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
        if payload["raw_variant_count"] != 8:
            raise AssertionError("unexpected raw_variant_count in exploratory matrix")
        if payload["variant_count"] != 3:
            raise AssertionError("budget pruning did not limit exploratory matrix size")
        if payload["pruned_variant_count"] != 5:
            raise AssertionError("pruned_variant_count did not capture discarded candidates")
        if payload["current_research"] != "main@abc1234":
            raise AssertionError("current_research was not preserved")
        if payload["baseline_ref"] != "main@abc1234":
            raise AssertionError("baseline_ref compatibility alias was not preserved")
        if payload["variants"][0]["subset_size"] != 128:
            raise AssertionError("subset size was not preserved")
        if payload["variants"][0]["id"] != "variant-007":
            raise AssertionError("tri-factor ranking did not prioritize the strongest pre-execution candidate")
        if payload["variants"][0]["short_run_steps"] is not None:
            raise AssertionError("tri-factor ranking should still keep the best selected candidate within budget")
        if sorted(payload["variants"][0]["axes"]) != ["adapter", "lr"]:
            raise AssertionError("variant axes were not preserved")
        if payload["variants"][0]["current_research"] != "main@abc1234":
            raise AssertionError("variant current_research was not propagated")
        if payload["variants"][0]["predicted_success_score"] <= 0:
            raise AssertionError("variant predicted_success_score was not recorded")
        if payload["variants"][0]["predicted_gain_score"] <= 0:
            raise AssertionError("variant predicted_gain_score was not recorded")
        if payload["variants"][0]["total_score"] <= 0:
            raise AssertionError("variant total_score was not recorded")
        if payload["metric_policy"]["primary_metric"] != "val_loss":
            raise AssertionError("metric policy lost primary_metric")
        if payload["metric_policy"]["metric_goal"] != "minimize":
            raise AssertionError("metric policy failed to normalize metric_goal")
        if payload["variant_budget"]["max_variants"] != 3:
            raise AssertionError("variant budget lost max_variants")
        if payload["variant_budget"]["max_short_cycle_runs"] != 1:
            raise AssertionError("variant budget lost max_short_cycle_runs")
        if payload["selection_policy"]["factors"] != ["cost", "success_rate", "expected_gain"]:
            raise AssertionError("selection policy lost factor ordering")
        if payload["selection_policy"]["weights"]["expected_gain"] != 0.4:
            raise AssertionError("selection policy lost normalized weights")
        if sum(1 for item in payload["variants"] if item["short_run_steps"] is not None) > 1:
            raise AssertionError("short-cycle budget did not cap the number of executed short-run candidates")

        print("ok: True")
        print("checks: 16")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())
