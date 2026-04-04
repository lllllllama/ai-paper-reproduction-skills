#!/usr/bin/env python3
"""Regression checks for atomic idea decomposition."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "skills" / "ai-research-explore" / "scripts"
    sys.path.insert(0, str(scripts_dir))
    from passes.atomic_idea_decomposition import run_atomic_idea_decomposition_pass

    temp_root = Path(tempfile.mkdtemp(prefix="codex-atomic-idea-map-", dir=repo_root))
    try:
        analysis_output_dir = temp_root / "analysis_outputs"
        analysis_output_dir.mkdir(parents=True, exist_ok=True)

        selected_idea = {
            "id": "idea-001",
            "summary": "Transplant the adapter block with a bounded config-controlled shim.",
            "change_scope": "adapter_block",
            "target_component": "adapter",
            "source_reference": ["paper:abc12345"],
            "implementation_risk": 0.2,
            "eval_risk": 0.1,
        }
        analysis_data = {
            "config_binding_hints": ["configs/demo.yaml"],
            "constructor_candidates": ["models/adapter.py:AdapterBlock"],
            "forward_candidates": ["models/adapter.py:AdapterBlock.forward"],
            "module_files": ["models/adapter.py"],
        }
        source_mapping = {
            "selected_source_record": {
                "source_id": "paper:abc12345",
                "source_repo": "org/source-repo",
                "source_file": "upstream/adapter.py",
                "source_symbol": "AdapterBlock",
            },
            "target_location_map": [
                {"file": "models/adapter.py", "target_symbol": "models/adapter.py:AdapterBlock", "role": "code"},
                {"file": "configs/demo.yaml", "target_symbol": "adapter_block", "role": "config"},
            ],
            "module_candidates": [
                {"target_file": "models/adapter.py", "target_symbol": "models/adapter.py:AdapterBlock"}
            ],
        }
        lookup_bundle = {
            "records": [
                {"source_id": "paper:abc12345", "title": "Adapter Paper", "evidence_class": "external_provider"}
            ]
        }
        bundle = run_atomic_idea_decomposition_pass(
            analysis_output_dir=analysis_output_dir,
            selected_idea=selected_idea,
            analysis_data=analysis_data,
            source_mapping=source_mapping,
            lookup_bundle=lookup_bundle,
            current_research="main@abc1234",
            variant_spec={"base_command": "python train.py --config configs/demo.yaml"},
        )
        if bundle["status"] != "ready":
            raise AssertionError("atomic decomposition should succeed for a bounded selected idea")
        if bundle["atomic_unit_count"] < 2:
            raise AssertionError("atomic decomposition should split code and config surfaces into separate units")
        first_unit = bundle["atomic_units"][0]
        for key in [
            "atomic_id",
            "concept_name",
            "formula_support",
            "code_support",
            "target_file_candidates",
            "validation_strategy",
            "scientific_meaning_risk",
        ]:
            if key not in first_unit:
                raise AssertionError(f"atomic decomposition lost required field `{key}`")
        if not (analysis_output_dir / "ATOMIC_IDEA_MAP.md").exists():
            raise AssertionError("atomic decomposition did not write ATOMIC_IDEA_MAP.md")
        if not (analysis_output_dir / "ATOMIC_IDEA_MAP.json").exists():
            raise AssertionError("atomic decomposition did not write ATOMIC_IDEA_MAP.json")

        blocked = run_atomic_idea_decomposition_pass(
            analysis_output_dir=analysis_output_dir,
            selected_idea={
                "id": "idea-bad",
                "summary": "Rewrite everything.",
                "change_scope": "broad_rewrite",
                "target_component": "trainer",
            },
            analysis_data={},
            source_mapping={},
            lookup_bundle={"records": []},
            current_research="main@abc1234",
            variant_spec={},
        )
        if blocked["status"] != "blocked":
            raise AssertionError("atomic decomposition should block overly broad or targetless ideas")
        if not blocked["blockers"]:
            raise AssertionError("atomic decomposition should emit explicit blockers")

        print("ok: True")
        print("checks: 6")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())

