#!/usr/bin/env python3
"""Regression checks for implementation fidelity summaries."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "skills" / "ai-research-explore" / "scripts"
    sys.path.insert(0, str(scripts_dir))
    from passes.implementation_fidelity import run_implementation_fidelity_pass

    temp_root = Path(tempfile.mkdtemp(prefix="codex-implementation-fidelity-", dir=repo_root))
    try:
        analysis_output_dir = temp_root / "analysis_outputs"
        analysis_output_dir.mkdir(parents=True, exist_ok=True)
        selected_idea = {"id": "idea-001", "change_scope": "lora_rank"}
        atomic_bundle = {
            "status": "ready",
            "atomic_units": [
                {
                    "atomic_id": "idea-001-atomic-01",
                    "concept_name": "Adapter Rank",
                    "expected_code_surface": "model",
                    "target_file_candidates": ["models/adapter.py"],
                    "target_symbol_candidates": ["AdapterBlock.forward"],
                },
                {
                    "atomic_id": "idea-001-atomic-02",
                    "concept_name": "Rank Control Surface",
                    "expected_code_surface": "config",
                    "target_file_candidates": ["configs/demo.yaml"],
                    "target_symbol_candidates": ["lora_rank"],
                },
            ],
            "blockers": [],
        }
        source_mapping = {
            "target_location_map": [{"file": "models/adapter.py"}],
            "minimal_patch_plan": [{"target_files": ["models/adapter.py"]}],
        }
        code_plan = {"candidate_edit_targets": ["models/adapter.py", "configs/demo.yaml"]}

        pre = run_implementation_fidelity_pass(
            analysis_output_dir=analysis_output_dir,
            selected_idea=selected_idea,
            atomic_bundle=atomic_bundle,
            source_mapping=source_mapping,
            code_plan=code_plan,
            experiment_manifest={},
            executed_runs=[],
            phase="pre-execution",
        )
        pre_model_unit = next(item for item in pre["fidelity_units"] if item["expected_implementation_site"]["surface"] == "model")
        if pre_model_unit["fidelity_state"] != "not-started":
            raise AssertionError("pre-execution fidelity should stay in not-started state")
        if pre_model_unit["verification_level"] != "planned_only":
            raise AssertionError("pre-execution fidelity should record planned_only verification")
        if pre_model_unit["observed_implementation_sites"]:
            raise AssertionError("pre-execution fidelity should not surface observed implementation sites")

        heuristic = run_implementation_fidelity_pass(
            analysis_output_dir=analysis_output_dir,
            selected_idea=selected_idea,
            atomic_bundle=atomic_bundle,
            source_mapping=source_mapping,
            code_plan=code_plan,
            experiment_manifest={"config_overrides": {"lora_rank": "8"}, "changed_files": ["models/adapter.py"]},
            executed_runs=[{"id": "variant-001", "axes": {"lora_rank": "8"}}],
            phase="post-execution",
        )
        config_unit = next(item for item in heuristic["fidelity_units"] if item["expected_implementation_site"]["surface"] == "config")
        model_unit = next(item for item in heuristic["fidelity_units"] if item["expected_implementation_site"]["surface"] == "model")
        if config_unit["fidelity_state"] != "partial":
            raise AssertionError("config fidelity should become partial when only runtime overrides were observed")
        if config_unit["verification_level"] != "heuristic_only":
            raise AssertionError("config fidelity should stay heuristic_only without a diff")
        if not config_unit["heuristic_implementation_sites"]:
            raise AssertionError("config fidelity should surface heuristic implementation sites")
        if config_unit["observed_implementation_sites"]:
            raise AssertionError("planned or heuristic config data must not enter observed implementation sites")
        if model_unit["verification_level"] != "planned_only":
            raise AssertionError("model fidelity should remain planned_only without diff evidence")
        if model_unit["observed_implementation_sites"]:
            raise AssertionError("planned edit targets must not enter observed implementation sites")

        observed = run_implementation_fidelity_pass(
            analysis_output_dir=analysis_output_dir,
            selected_idea=selected_idea,
            atomic_bundle=atomic_bundle,
            source_mapping={},
            code_plan={},
            experiment_manifest={},
            executed_runs=[{"id": "variant-002", "touched_paths": ["models/adapter.py"]}],
            phase="post-execution",
        )
        observed_model_unit = next(
            item for item in observed["fidelity_units"] if item["expected_implementation_site"]["surface"] == "model"
        )
        if observed_model_unit["verification_level"] != "executor_observed":
            raise AssertionError("executor touched-path evidence should be marked executor_observed")
        if not observed_model_unit["observed_implementation_sites"]:
            raise AssertionError("executor touched-path evidence should surface observed implementation sites")

        verified = run_implementation_fidelity_pass(
            analysis_output_dir=analysis_output_dir,
            selected_idea=selected_idea,
            atomic_bundle=atomic_bundle,
            source_mapping={},
            code_plan={},
            experiment_manifest={},
            executed_runs=[{"id": "variant-003", "changed_files": ["models/adapter.py"]}],
            phase="post-execution",
        )
        verified_model_unit = next(
            item for item in verified["fidelity_units"] if item["expected_implementation_site"]["surface"] == "model"
        )
        if verified_model_unit["verification_level"] != "diff_verified":
            raise AssertionError("changed-file evidence should be recorded as diff_verified")
        if verified_model_unit["fidelity_state"] != "likely-implemented":
            raise AssertionError("diff-verified changed-file evidence should surface likely-implemented fidelity")
        if not (analysis_output_dir / "IMPLEMENTATION_FIDELITY.md").exists():
            raise AssertionError("implementation fidelity did not write IMPLEMENTATION_FIDELITY.md")
        if not (analysis_output_dir / "IMPLEMENTATION_FIDELITY.json").exists():
            raise AssertionError("implementation fidelity did not write IMPLEMENTATION_FIDELITY.json")

        rendered = json.loads((analysis_output_dir / "IMPLEMENTATION_FIDELITY.json").read_text(encoding="utf-8"))
        if rendered["fidelity_units"][0]["verification_level"] not in (analysis_output_dir / "IMPLEMENTATION_FIDELITY.md").read_text(encoding="utf-8"):
            raise AssertionError("implementation fidelity markdown lost verification_level details")
        if rendered["fidelity_units"][0]["fidelity_state"] not in (analysis_output_dir / "IMPLEMENTATION_FIDELITY.md").read_text(encoding="utf-8"):
            raise AssertionError("implementation fidelity markdown lost fidelity_state details")

        print("ok: True")
        print("checks: 17")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())
