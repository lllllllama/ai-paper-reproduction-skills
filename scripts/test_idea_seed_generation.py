#!/usr/bin/env python3
"""Regression checks for bounded idea seed generation."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "skills" / "ai-research-explore" / "scripts"
    sys.path.insert(0, str(scripts_dir))
    from passes.candidate_idea_generation import run_candidate_idea_generation_pass
    from passes.idea_cards import run_idea_card_pass
    from passes.idea_ranking import run_idea_ranking_pass
    from passes.improvement_bank import run_improvement_bank_pass

    temp_root = Path(tempfile.mkdtemp(prefix="codex-idea-seeds-", dir=repo_root))
    try:
        analysis_output_dir = temp_root / "analysis_outputs"
        analysis_output_dir.mkdir(parents=True, exist_ok=True)
        analysis_data = {
            "config_binding_hints": ["configs/demo.yaml"],
            "module_files": ["models/adapter.py", "models/head.py"],
            "constructor_candidates": ["models/adapter.py:AdapterBlock"],
            "forward_candidates": ["models/adapter.py:AdapterBlock.forward"],
            "symbol_hints": ["AdapterBlock", "SegHead"],
        }
        lookup_bundle = {
            "records": [
                {
                    "source_id": "paper:ext11111",
                    "title": "Adapter Paper",
                    "summary": "adapter block transplant",
                    "query": "adapter block",
                    "provider_type": "github",
                    "evidence_class": "external_provider",
                    "evidence_weight": 1.0,
                }
            ],
            "support_bundle": {"support_index_by_candidate_idea": {}},
        }
        variant_spec = {
            "variant_axes": {"lora_rank": ["4", "8"], "adapter_dropout": ["0.0", "0.1"]},
            "base_command": "python train.py --config configs/demo.yaml",
        }
        campaign = {"evaluation_source": {"command": "python eval.py --config configs/demo.yaml"}}
        code_plan = {"candidate_edit_targets": ["models/adapter.py", "configs/demo.yaml"]}

        researcher_bank = run_improvement_bank_pass(
            analysis_output_dir=analysis_output_dir,
            campaign=campaign,
            analysis_data=analysis_data,
            code_plan=code_plan,
            lookup_bundle=lookup_bundle,
            baseline_gate={"decision": "proceed"},
            candidate_ideas=[],
        )
        generated_only = run_candidate_idea_generation_pass(
            analysis_output_dir=analysis_output_dir,
            current_research="main@abc1234",
            task_family="segmentation",
            dataset="DemoSeg",
            evaluation_source=campaign["evaluation_source"],
            variant_spec=variant_spec,
            analysis_data=analysis_data,
            improvement_bank=researcher_bank,
            researcher_candidate_ideas=[],
            idea_generation={},
        )
        if generated_only["researcher_ideas"]:
            raise AssertionError("seed generation should not invent researcher ideas")
        if not generated_only["generated_ideas"]:
            raise AssertionError("seed generation should synthesize ideas when the researcher did not provide any")
        if generated_only["generated_ideas"][0]["seed_origin"] != "synthesized":
            raise AssertionError("seed generation should mark fallback ideas as synthesized")
        for key in [
            "id",
            "summary",
            "seed_origin",
            "context_anchor",
            "task_family_binding",
            "dataset_binding",
            "evaluation_binding",
            "constraint_notes",
        ]:
            if key not in generated_only["generated_ideas"][0]:
                raise AssertionError(f"seed generation lost required seed field `{key}`")

        researcher_ideas = [
            {
                "id": "idea-001",
                "summary": "Tune the adapter rank while keeping the decoder unchanged.",
                "change_scope": "lora_rank",
                "target_component": "adapter",
                "expected_upside": 0.82,
                "implementation_risk": 0.20,
                "eval_risk": 0.10,
                "rollback_ease": 0.90,
                "estimated_runtime_cost": 0.30,
                "single_variable_fit": 0.95,
                "seed_origin": "researcher",
            }
        ]
        researcher_bank = run_improvement_bank_pass(
            analysis_output_dir=analysis_output_dir,
            campaign=campaign,
            analysis_data=analysis_data,
            code_plan=code_plan,
            lookup_bundle=lookup_bundle,
            baseline_gate={"decision": "proceed"},
            candidate_ideas=researcher_ideas,
        )
        generated = run_candidate_idea_generation_pass(
            analysis_output_dir=analysis_output_dir,
            current_research="main@abc1234",
            task_family="segmentation",
            dataset="DemoSeg",
            evaluation_source=campaign["evaluation_source"],
            variant_spec=variant_spec,
            analysis_data=analysis_data,
            improvement_bank=researcher_bank,
            researcher_candidate_ideas=researcher_ideas,
            idea_generation={},
        )
        if len(generated["researcher_ideas"]) != 1:
            raise AssertionError("seed generation should preserve researcher ideas")
        if len(generated["generated_ideas"]) <= 0:
            raise AssertionError("seed generation should top up synthesized or hybrid ideas")
        merged_bank = run_improvement_bank_pass(
            analysis_output_dir=analysis_output_dir,
            campaign=campaign,
            analysis_data=analysis_data,
            code_plan=code_plan,
            lookup_bundle=lookup_bundle,
            baseline_gate={"decision": "proceed"},
            candidate_ideas=generated["all_seed_ideas"],
        )
        cards = run_idea_card_pass(
            analysis_output_dir=analysis_output_dir,
            improvement_items=merged_bank["items"],
        )
        ranking = run_idea_ranking_pass(
            analysis_output_dir=analysis_output_dir,
            cards=cards["cards"],
            baseline_gate={"decision": "proceed"},
        )
        if ranking["selected_idea"]["seed_origin"] != "researcher":
            raise AssertionError("researcher hard precedence should keep final selection inside the researcher pool")
        if ranking["active_selection_pool"] != "researcher":
            raise AssertionError("ranking should record the active selection pool")
        artifact = (analysis_output_dir / "IDEA_SEEDS.json").read_text(encoding="utf-8")
        if "context_anchor" not in artifact or "evaluation_binding" not in artifact:
            raise AssertionError("IDEA_SEEDS.json lost context binding fields")

        print("ok: True")
        print("checks: 10")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())

