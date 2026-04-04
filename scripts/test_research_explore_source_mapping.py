#!/usr/bin/env python3
"""Regression checks for source mapping and minimal patch planning."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "skills" / "ai-research-explore" / "scripts"
    sys.path.insert(0, str(scripts_dir))
    from passes.source_mapping import run_source_mapping_pass

    temp_root = Path(tempfile.mkdtemp(prefix="codex-source-mapping-", dir=repo_root))
    try:
        analysis_output_dir = temp_root / "analysis_outputs"
        analysis_output_dir.mkdir(parents=True, exist_ok=True)

        selected_idea = {
            "id": "idea-001",
            "summary": "Transplant the adapter block with a thin shim.",
            "change_scope": "adapter_block",
            "target_component": "adapter",
            "source_reference": ["paper:abc12345"],
        }
        analysis_data = {
            "constructor_candidates": ["AdapterBlock.__init__", "Head.__init__"],
            "forward_candidates": ["AdapterBlock.forward"],
            "config_binding_hints": ["configs/demo.yaml"],
            "module_files": ["models/adapter.py", "models/head.py"],
            "metric_files": ["eval.py"],
        }
        code_plan = {
            "candidate_edit_targets": ["models/adapter.py", "configs/demo.yaml"],
            "source_repo_refs": [{"repo": "org/source-repo", "ref": "deadbeef"}],
        }
        lookup_bundle = {
            "records": [
                {
                    "source_id": "paper:abc12345",
                    "title": "Adapter Paper",
                    "source_repo": "openai/gym",
                    "source_file": "gym/core.py",
                    "source_symbol": "Env",
                },
            ]
        }
        variant_matrix = {"base_command": "python train.py --config configs/demo.yaml"}

        bundle = run_source_mapping_pass(
            analysis_output_dir=analysis_output_dir,
            selected_idea=selected_idea,
            analysis_data=analysis_data,
            code_plan=code_plan,
            lookup_bundle=lookup_bundle,
            variant_matrix=variant_matrix,
        )

        if not bundle["target_location_map"]:
            raise AssertionError("source mapping did not produce target locations")
        if bundle["module_candidates"][0]["target_file"] != "models/adapter.py":
            raise AssertionError("source mapping chose the wrong target file")
        change_types = {item["change_type"] for item in bundle["minimal_patch_plan"]}
        if "import-glue" not in change_types:
            raise AssertionError("source mapping lost import-glue patch planning")
        if "protected-zone-no-touch" not in change_types:
            raise AssertionError("source mapping lost protected-zone planning")
        if bundle["transplant_ready"] is not True:
            raise AssertionError("source mapping should allow the transplant path when the source triple is complete")
        if bundle["resolved_patch_class"] != "module-transplant-shim":
            raise AssertionError("source mapping should resolve patch_class from the final transplant plan")
        smoke_names = {item["name"] for item in bundle["smoke_plan"]}
        if {"syntax-parse", "short-run-command"} - smoke_names:
            raise AssertionError("source mapping lost smoke-plan coverage")
        if not (analysis_output_dir / "MODULE_CANDIDATES.md").exists():
            raise AssertionError("source mapping did not write MODULE_CANDIDATES.md")
        if not (analysis_output_dir / "INTERFACE_DIFF.md").exists():
            raise AssertionError("source mapping did not write INTERFACE_DIFF.md")

        blocked_bundle = run_source_mapping_pass(
            analysis_output_dir=analysis_output_dir,
            selected_idea=selected_idea,
            analysis_data=analysis_data,
            code_plan=code_plan,
            lookup_bundle={"records": [{"source_id": "paper:abc12345", "title": "Adapter Paper"}]},
            variant_matrix=variant_matrix,
        )
        blocked_types = {item["change_type"] for item in blocked_bundle["minimal_patch_plan"]}
        if "module-transplant-shim" in blocked_types:
            raise AssertionError("source mapping should not enter the transplant path without a source triple")
        if "transplant-blocked" not in blocked_types:
            raise AssertionError("source mapping should explain why the transplant path was blocked")
        if blocked_bundle["resolved_patch_class"] != "module-transplant-shim":
            raise AssertionError("source mapping should keep the transplant classification even when the path is blocked by a missing source triple")

        print("ok: True")
        print("checks: 12")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())

