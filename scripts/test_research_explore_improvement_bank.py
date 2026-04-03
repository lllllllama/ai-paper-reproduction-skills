#!/usr/bin/env python3
"""Regression checks for improvement mining, idea cards, and ranking."""

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
    from passes.idea_cards import run_idea_card_pass
    from passes.idea_ranking import run_idea_ranking_pass

    temp_root = Path(tempfile.mkdtemp(prefix="codex-improvement-bank-", dir=repo_root))
    try:
        analysis_output_dir = temp_root / "analysis_outputs"
        analysis_output_dir.mkdir(parents=True, exist_ok=True)

        campaign = {
            "task_family": "segmentation",
            "evaluation_source": {"command": "python eval.py --config configs/demo.yaml"},
            "candidate_ideas": [
                {
                    "id": "idea-001",
                    "summary": "Replace the adapter block with a slimmer transplant.",
                    "change_scope": "adapter_block",
                    "target_component": "adapter",
                    "expected_upside": 0.8,
                    "implementation_risk": 0.2,
                    "eval_risk": 0.1,
                    "rollback_ease": 0.9,
                    "estimated_runtime_cost": 0.3,
                    "single_variable_fit": 0.95,
                },
                {
                    "id": "idea-002",
                    "summary": "Rewrite the training loop and add auxiliary heads.",
                    "change_scope": "training_loop",
                    "target_component": "trainer",
                    "expected_upside": 0.5,
                    "implementation_risk": 0.7,
                    "eval_risk": 0.75,
                    "rollback_ease": 0.2,
                    "estimated_runtime_cost": 0.8,
                    "single_variable_fit": 0.4,
                },
            ],
        }
        analysis_data = {
            "symbol_hints": ["AdapterBlock", "Trainer"],
            "constructor_candidates": ["AdapterBlock.__init__"],
            "forward_candidates": ["AdapterBlock.forward"],
            "module_files": ["models/adapter.py", "trainer.py"],
        }
        code_plan = {
            "candidate_edit_targets": ["models/adapter.py", "configs/demo.yaml"],
        }
        lookup_bundle = {
            "records": [
                {
                    "source_id": "paper:aaa11111",
                    "title": "Adapter Transplant",
                    "summary": "adapter block transplant",
                    "query": "adapter transplant",
                    "provider_type": "github",
                    "evidence_class": "external_provider",
                    "evidence_weight": 1.0,
                },
                {
                    "source_id": "repo:bbb22222",
                    "title": "Adapter Repo",
                    "summary": "adapter implementation",
                    "query": "adapter repo",
                    "provider_type": "seed",
                    "evidence_class": "seed_only",
                    "evidence_weight": 0.2,
                },
            ],
            "support_bundle": {
                "support_index_by_candidate_idea": {
                    "idea-001": {
                        "matched_source_ids": ["paper:aaa11111", "repo:bbb22222"],
                    }
                }
            },
        }
        baseline_gate = {"decision": "proceed", "gap_to_sota": 0.8}

        improvement_bank = run_improvement_bank_pass(
            analysis_output_dir=analysis_output_dir,
            campaign=campaign,
            analysis_data=analysis_data,
            code_plan=code_plan,
            lookup_bundle=lookup_bundle,
            baseline_gate=baseline_gate,
        )
        idea_cards = run_idea_card_pass(
            analysis_output_dir=analysis_output_dir,
            improvement_items=improvement_bank["items"],
        )
        idea_gate = run_idea_ranking_pass(
            analysis_output_dir=analysis_output_dir,
            cards=idea_cards["cards"],
            baseline_gate=baseline_gate,
        )

        if not (analysis_output_dir / "IMPROVEMENT_BANK.md").exists():
            raise AssertionError("improvement bank did not write IMPROVEMENT_BANK.md")
        if not (analysis_output_dir / "IDEA_CARDS.json").exists():
            raise AssertionError("idea-card pass did not write IDEA_CARDS.json")
        if not (analysis_output_dir / "IDEA_EVALUATION.md").exists():
            raise AssertionError("idea ranking did not write IDEA_EVALUATION.md")
        if idea_gate["selected_idea"]["id"] != "idea-001":
            raise AssertionError("idea ranking selected the wrong idea")
        if not idea_gate["ranked_ideas"][0]["hard_gate_passed"]:
            raise AssertionError("top idea should have passed hard gates")
        if "eval-risk" not in idea_gate["ranked_ideas"][1]["hard_gate_failures"]:
            raise AssertionError("weak idea should have failed eval-risk gate")
        if "single_variable_fit" not in idea_cards["cards"][0]:
            raise AssertionError("idea cards lost required fields")
        if not improvement_bank["items"][0]["source_reference"]:
            raise AssertionError("improvement bank lost source references")
        if idea_cards["cards"][0]["patch_class"] != "config-only":
            raise AssertionError("idea cards should default to a conservative patch_class before source mapping resolves the path")
        if improvement_bank["items"][0]["external_source_reference"] != ["paper:aaa11111"]:
            raise AssertionError("improvement bank failed to separate external evidence from seed-only evidence")
        if improvement_bank["items"][0]["source_evidence_summary"]["seed_only_records"] != 1:
            raise AssertionError("improvement bank lost the seed-only evidence count")
        if improvement_bank["items"][0]["source_support_strength"] >= 0.6:
            raise AssertionError("seed-only evidence still inflates source support too aggressively")

        print("ok: True")
        print("checks: 12")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())
