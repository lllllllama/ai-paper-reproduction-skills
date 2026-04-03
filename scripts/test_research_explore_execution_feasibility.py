#!/usr/bin/env python3
"""Regression checks for execution feasibility and resource planning."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "skills" / "research-explore" / "scripts"
    sys.path.insert(0, str(scripts_dir))
    from passes.execution_feasibility import run_execution_feasibility_pass

    temp_root = Path(tempfile.mkdtemp(prefix="codex-feasibility-", dir=repo_root))
    try:
        repo_path = temp_root / "sample_repo"
        repo_path.mkdir(parents=True, exist_ok=True)
        (repo_path / "model.py").write_text("class Demo:\n    pass\n", encoding="utf-8")
        (repo_path / "train.py").write_text("print('train')\n", encoding="utf-8")
        (repo_path / "configs").mkdir()
        (repo_path / "configs" / "demo.yaml").write_text("model: demo\n", encoding="utf-8")

        analysis_output_dir = temp_root / "analysis_outputs"
        analysis_output_dir.mkdir(parents=True, exist_ok=True)
        campaign = {
            "compute_budget": {"max_runtime_hours": 1},
            "execution_policy": {"max_executed_variants": 1, "variant_timeout": 300},
        }
        analysis_data = {
            "constructor_candidates": ["Demo.__init__"],
            "forward_candidates": ["Demo.forward"],
        }
        variant_matrix = {
            "base_command": "python train.py --config configs/demo.yaml",
            "variant_count": 1,
        }
        source_mapping = {
            "target_location_map": [{"file": "model.py", "target_symbol": "Demo.__init__", "role": "code"}],
            "smoke_plan": [{"name": "syntax-parse", "scope": ["model.py"]}],
        }

        bundle = run_execution_feasibility_pass(
            analysis_output_dir=analysis_output_dir,
            repo_path=repo_path,
            campaign=campaign,
            analysis_data=analysis_data,
            variant_matrix=variant_matrix,
            source_mapping=source_mapping,
            executed_runs=[],
        )
        blocked = run_execution_feasibility_pass(
            analysis_output_dir=analysis_output_dir,
            repo_path=repo_path,
            campaign=campaign,
            analysis_data=analysis_data,
            variant_matrix={"base_command": "", "variant_count": 0},
            source_mapping=source_mapping,
            executed_runs=[],
        )

        if not (analysis_output_dir / "RESOURCE_PLAN.md").exists():
            raise AssertionError("execution feasibility did not write RESOURCE_PLAN.md")
        if bundle["feasibility"]["short_run_feasibility"] != "proceed":
            raise AssertionError("execution feasibility blocked a runnable short-run plan")
        if bundle["static_smoke"]["status"] != "passed":
            raise AssertionError("execution feasibility lost static smoke status")
        if bundle["runtime_smoke"]["status"] != "planned":
            raise AssertionError("execution feasibility lost runtime smoke status")
        runtime_checks = {item["name"]: item for item in bundle["runtime_smoke"]["checks"]}
        if runtime_checks["import-probe"]["status"] != "passed":
            raise AssertionError("execution feasibility did not run the import probe")
        if runtime_checks["constructor-probe"]["status"] != "passed":
            raise AssertionError("execution feasibility did not run the constructor probe")
        if bundle["smoke_report"]["status"] != "planned":
            raise AssertionError("execution feasibility lost combined smoke report status")
        if "parallel_strategy" not in bundle["recommendations"]:
            raise AssertionError("execution feasibility lost acceleration recommendations")
        if "cpu" not in bundle["resources"]:
            raise AssertionError("execution feasibility lost resource detection")
        if blocked["feasibility"]["short_run_feasibility"] != "blocked":
            raise AssertionError("execution feasibility failed to block a missing base command")

        print("ok: True")
        print("checks: 10")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())
