#!/usr/bin/env python3
"""Checks for evidence layering and seed-only downweighting."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "skills" / "research-explore" / "scripts"
    sys.path.insert(0, str(scripts_dir))
    from passes.improvement_bank import run_improvement_bank_pass

    temp_root = Path(tempfile.mkdtemp(prefix="codex-evidence-layers-", dir=repo_root))
    try:
        analysis_output_dir = temp_root / "analysis_outputs"
        analysis_output_dir.mkdir(parents=True, exist_ok=True)
        campaign = {
            "task_family": "segmentation",
            "evaluation_source": {"command": "python eval.py --config configs/demo.yaml"},
            "candidate_ideas": [
                {
                    "id": "idea-001",
                    "summary": "Transplant the adapter block.",
                    "change_scope": "adapter_block",
                    "target_component": "adapter",
                    "expected_upside": 0.8,
                    "implementation_risk": 0.2,
                    "eval_risk": 0.1,
                    "rollback_ease": 0.9,
                    "estimated_runtime_cost": 0.3,
                    "single_variable_fit": 0.95,
                }
            ],
        }
        lookup_bundle = {
            "records": [
                {"source_id": "paper:ext11111", "title": "Adapter Paper", "summary": "adapter", "evidence_class": "external_provider", "evidence_weight": 1.0},
                {"source_id": "paper:par22222", "title": "Adapter Locator", "summary": "adapter", "evidence_class": "parsed_locator", "evidence_weight": 0.65},
                {"source_id": "paper:loc33333", "title": "Adapter Repo-local", "summary": "adapter", "evidence_class": "repo_local_extracted", "evidence_weight": 0.45},
                {"source_id": "paper:seed4444", "title": "Adapter Seed", "summary": "adapter", "evidence_class": "seed_only", "evidence_weight": 0.2},
            ],
            "support_bundle": {
                "support_index_by_candidate_idea": {
                    "idea-001": {
                        "matched_source_ids": ["paper:ext11111", "paper:par22222", "paper:loc33333", "paper:seed4444"],
                    }
                }
            },
        }
        bank = run_improvement_bank_pass(
            analysis_output_dir=analysis_output_dir,
            campaign=campaign,
            analysis_data={"module_files": ["model.py"]},
            code_plan={"candidate_edit_targets": ["model.py"]},
            lookup_bundle=lookup_bundle,
            baseline_gate={"decision": "proceed", "gap_to_sota": 0.4},
        )
        item = bank["items"][0]
        if item["source_evidence_summary"]["external_provider_records"] != 1:
            raise AssertionError("evidence summary lost external provider count")
        if item["source_evidence_summary"]["parsed_locator_records"] != 1:
            raise AssertionError("evidence summary lost parsed locator count")
        if item["source_evidence_summary"]["repo_local_extracted_records"] != 1:
            raise AssertionError("evidence summary lost repo-local count")
        if item["source_evidence_summary"]["seed_only_records"] != 1:
            raise AssertionError("evidence summary lost seed-only count")
        if item["source_support_strength"] <= 0.4:
            raise AssertionError("external/parsed/repo-local evidence should materially improve support strength")

        print("ok: True")
        print("checks: 5")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())
