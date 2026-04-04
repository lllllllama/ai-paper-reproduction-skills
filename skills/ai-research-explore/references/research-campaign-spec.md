# Research Campaign Spec

## Purpose

Use `research_campaign.json` or `research_campaign.yaml` when `ai-research-explore` is operating in the third scenario:

- the task family is already chosen
- the dataset is already chosen
- the evaluation method is already chosen
- the provided SOTA table is already frozen by the researcher
- the remaining work is campaign governance, implementation, and candidate filtering

`variant_spec` still exists, but it is now the run-level part of a larger campaign.

## Minimal Shape

```json
{
  "current_research": "seg-branch@abc1234",
  "task_family": "segmentation",
  "dataset": "DemoSeg",
  "benchmark": {
    "name": "DemoBench",
    "primary_metric": "miou",
    "metric_goal": "maximize"
  },
  "evaluation_source": {
    "command": "python eval.py --config configs/demo.yaml",
    "path": "eval.py",
    "primary_metric": "miou",
    "metric_goal": "maximize"
  },
  "sota_reference": [
    {
      "name": "Provided SOTA",
      "metric": "miou",
      "value": 80.0,
      "source": "paper-or-table-url"
    }
  ],
  "candidate_ideas": [
    {
      "id": "idea-lora-rank",
      "summary": "Increase LoRA rank while keeping the decoder unchanged.",
      "change_scope": "lora_rank",
      "target_component": "segmentation_head",
      "expected_upside": 0.85,
      "implementation_risk": 0.20,
      "eval_risk": 0.15,
      "rollback_ease": 0.90,
      "estimated_runtime_cost": 0.35,
      "single_variable_fit": 0.95
    }
  ],
  "compute_budget": {
    "max_runtime_hours": 8
  },
  "baseline_gate": {
    "abandon_gap": 2.0
  },
  "execution_policy": {
    "run_selected_variants": true,
    "max_executed_variants": 2,
    "variant_timeout": 1800
  },
  "variant_spec": {
    "current_research": "seg-branch@abc1234",
    "base_command": "python train.py --config configs/demo.yaml",
    "variant_axes": {
      "lora_rank": ["4", "8"]
    },
    "subset_sizes": [64],
    "short_run_steps": [100],
    "max_variants": 2,
    "max_short_cycle_runs": 1,
    "primary_metric": "miou",
    "metric_goal": "maximize"
  }
}
```

## Required Top-Level Fields

- `current_research`
  Durable anchor for the current research state.
- `task_family`
  The already-chosen task family, such as `segmentation`, `classification`, or `depth`.
- `dataset`
  The dataset name used for this campaign.
- `benchmark`
  The benchmark name or descriptor. A dictionary may also carry `primary_metric` and `metric_goal`.
- `evaluation_source`
  The frozen evaluation contract input. Prefer a command plus an optional path.
- `sota_reference`
  The user-provided comparison table. `ai-research-explore` treats this as authoritative input and does not prove completeness.
- `candidate_ideas`
  Preferred but optional candidate directions that the researcher already wants to consider. If omitted, or if `idea_generation.allow_synthesized_seed_ideas` stays enabled, the orchestrator may add a small number of conservative single-variable seed ideas.
- `variant_spec`
  The run-level candidate matrix used by `explore-run`.

Optional top-level fields:

- `research_lookup`
- `idea_policy`
- `idea_generation`
- `source_constraints`
- `feasibility_policy`

## `evaluation_source`

Supported fields:

- `command`
- `path`
- `primary_metric`
- `metric_goal`
- `execution_kind`
- `artifacts`
- `notes`
- `split`

This block feeds both:

- `analysis_outputs/EVAL_CONTRACT.md`
- the baseline gate

## `sota_reference`

Each item should preferably contain:

- `name`
- `metric`
- `value`

Optional fields:

- `source`
- `notes`
- `metric_goal`

This is a frozen comparison set for the campaign. It is not a guarantee that the real global SOTA has been fully covered.

## `candidate_ideas`

Each item should contain:

- `id`
- `summary`
- `change_scope`
- `target_component`
- `expected_upside`
- `implementation_risk`
- `eval_risk`
- `rollback_ease`
- `estimated_runtime_cost`
- `single_variable_fit`

Optional fields:

- `hypothesis`
- `supporting_changes`

The orchestrator uses these to run the idea gate. It does not treat them as novelty claims. When a researcher idea passes hard gates, final selection stays inside the researcher pool even if synthesized or hybrid ideas are also present for auditability.

## Optional Policy Blocks

### `research_lookup`

Use this block to seed auditable lookup records without turning the orchestrator into an open-ended research agent.

Supported fields:

- `queries`
- `seed_sources`
- `enable_repo_local_extraction`
- `optional_providers`

All lookup artifacts are cached into `sources/` with stable names, `sources/records/`, and an `index.json`. Missing optional provider keys must not block this pass.

### `idea_policy`

Optional governance hints for idea selection. Current implementations keep hard gates fixed and treat policy hints as future-compatible metadata.

Suggested fields:

- `max_patch_surface`
- `max_dependency_drag`
- `require_source_backing`

### `idea_generation`

Optional hints for bounded idea-space expansion. This block is additive; it should not break the minimal campaign shape.

Supported fields:

- `allow_synthesized_seed_ideas`
- `max_generated_ideas`
- `require_diverse_targets`

Default behavior keeps generation conservative:

- prefer single-variable ideas
- do not modify the frozen eval contract
- do not jump directly to broad architecture rewrites
- keep synthesized ideas bounded to repo-local components, existing variant axes, or lookup-backed source hints
- bind each generated seed to `current_research`, `task_family`, `dataset`, and `evaluation_source` in `IDEA_SEEDS.json`

### `source_constraints`

Optional hints for transplant scope.

Suggested fields:

- `preferred_repos`
- `forbidden_paths`
- `protected_zones`

### `feasibility_policy`

Optional hints for bounded execution.

Suggested fields:

- `prefer_short_run_only`
- `require_gpu`
- `max_short_run_hours`

## Gates

### Baseline gate

Default rules:

- `maximize`: abandon if baseline trails provided SOTA by more than `2.0` absolute points
- `minimize`: abandon if baseline is worse than provided SOTA by more than `5%`

The gate can return:

- `proceed`
- `borderline`
- `abandon`
- `not-applicable`

### Idea gate

Hard gates:

- `baseline_gate != abandon`
- `single_variable_fit >= 0.6`
- `interface_fit >= 0.5`
- `patch_surface <= 0.7`
- `dependency_drag <= 0.7`
- `eval_risk <= 0.6`
- `short_run_feasibility != blocked`

Soft ranking combines:

- `expected_upside`
- `single_variable_fit`
- `groundedness`
- `novelty_estimate`
- `interface_fit`
- `rollback_ease`
- `source_support_strength`
- `ablation_clarity`
- `implementation_story_clarity`
- `implementation_risk`
- `eval_risk`
- `estimated_runtime_cost`
- `patch_surface`
- `dependency_drag`
- `baseline_distance`

`IDEA_SCORES.json` records both raw inputs and explicit score breakdowns. If the active top-two ideas are too close, `ai-research-explore` records a human checkpoint instead of silently training.

If the selected idea cannot be decomposed into implementable atomic units, `ai-research-explore` records an explicit blocker/checkpoint such as `atomic-decomposition-blocked` and stops before broader implementation or execution.

## Output Expectations

Campaign mode writes:

- `analysis_outputs/RESEARCH_MAP.md`
- `analysis_outputs/CHANGE_MAP.md`
- `analysis_outputs/EVAL_CONTRACT.md`
- `analysis_outputs/SOURCE_INVENTORY.md`
- `analysis_outputs/SOURCE_SUPPORT.json`
- `analysis_outputs/IMPROVEMENT_BANK.md`
- `analysis_outputs/IDEA_CARDS.json`
- `analysis_outputs/IDEA_SEEDS.json`
- `analysis_outputs/IDEA_EVALUATION.md`
- `analysis_outputs/IDEA_SCORES.json`
- `analysis_outputs/MODULE_CANDIDATES.md`
- `analysis_outputs/INTERFACE_DIFF.md`
- `analysis_outputs/ATOMIC_IDEA_MAP.md`
- `analysis_outputs/ATOMIC_IDEA_MAP.json`
- `analysis_outputs/IMPLEMENTATION_FIDELITY.md`
- `analysis_outputs/IMPLEMENTATION_FIDELITY.json`
- `analysis_outputs/RESOURCE_PLAN.md`
- `analysis_outputs/status.json`
- `sources/index.json`
- `sources/SUMMARY.md`
- `sources/records/`
- `explore_outputs/CHANGESET.md`
- `explore_outputs/IDEA_GATE.md`
- `explore_outputs/EXPERIMENT_PLAN.md`
- `explore_outputs/EXPERIMENT_MANIFEST.md`
- `explore_outputs/EXPERIMENT_LEDGER.md`
- `explore_outputs/TRANSPLANT_SMOKE_REPORT.md`
- `explore_outputs/TOP_RUNS.md`
- `explore_outputs/status.json`

## Notes

- Keep idea generation bounded and auditable rather than open-ended.
- Keep evaluation and SOTA inputs human-frozen.
- `IDEA_SEEDS.json` should expose per-seed bindings such as `context_anchor`, `task_family_binding`, `dataset_binding`, `evaluation_binding`, and `constraint_notes`.
- `IMPLEMENTATION_FIDELITY.json` should separate `planned_implementation_sites`, `heuristic_implementation_sites`, and `observed_implementation_sites`, and should record `verification_level` as one of `not_checked`, `planned_only`, `heuristic_only`, `executor_observed`, or `diff_verified`.
- Let `ai-research-explore` focus on understanding, gating, implementation planning, controlled execution, and comparison.

