---
name: research-explore
description: Explore-lane end-to-end orchestrator for the third research scenario: the researcher has already chosen the task family, dataset, benchmark, evaluation method, and provided SOTA references, and wants candidate-only exploration on top of `current_research` with auditable repo understanding, idea gating, and governed experiments written to `explore_outputs/`. Do not use for README-first trusted reproduction, open-ended direction finding, narrow code-only or run-only exploration, passive repo analysis, or implicit experimentation.
---

# research-explore

## Workflow

- Accept either a legacy `variant_spec` flow or a higher-level `research_campaign` flow.
- Confirm `current_research` in a durable form such as a branch, commit, checkpoint, run record, or already-trained local model state.
- Keep all exploration on an isolated experiment branch or worktree.
- In campaign mode, always build repo-understanding artifacts that both the AI and the researcher can audit.
- Use `analyze-project` to produce `analysis_outputs/RESEARCH_MAP.md`, `CHANGE_MAP.md`, and `EVAL_CONTRACT.md`.
- Run the internal free-first, cache-first, provider-optional research lookup pass and cache auditable records into `sources/`; the built-in provider set is intentionally small and should be treated as bounded source resolution, not open-ended literature search.
- Convert bounded candidate ideas into a structured improvement bank and hypothesis cards.
- Use `env-and-assets-bootstrap` only when the environment or assets tied to `current_research` are still unclear.
- Run a baseline gate before candidate training when a campaign includes evaluation details and provided SOTA references.
- Run an idea gate before implementation; prefer one explicit single-variable idea over broad simultaneous changes and require source-backed cards.
- Use `explore-code` for bounded exploratory code adaptation.
- Build source mapping, heuristic interface diff, minimal reversible patch planning, and split static/runtime smoke validation before wider execution.
- Use `explore-run` for short-cycle trials, sweeps, and pre-execution candidate ranking.
- Run execution feasibility and resource checks before broader candidate runs.
- Let execution hand off to `minimal-run-and-audit` or `run-train` only when the exploratory plan needs real command execution.
- Build an `experiment_manifest` before wider execution and keep supporting changes mechanical and reversible.
- Write candidate-only outputs to `explore_outputs/`; never present the result as trusted reproduction success or a verified novelty/SOTA claim.

## Ranking Semantics

- Before execution, exploratory candidates should be prioritized with three factors: `cost`, `success_rate`, and `expected_gain`.
- Prefer using `selection_weights` in the variant spec when the researcher wants to rebalance those three factors.
- Keep budget limits explicit through `max_variants` and `max_short_cycle_runs`.
- After candidates actually run, rank results by real execution evidence: `status` first, then `primary_metric` and `metric_goal` when provided.
- In campaign mode, rank ideas separately from run variants. Hard gates should screen `single_variable_fit`, `interface_fit`, `patch_surface`, `dependency_drag`, `eval_risk`, and short-run feasibility before soft ranking.
- Soft idea ranking should prefer `expected_upside`, `single_variable_fit`, `interface_fit`, `rollback_ease`, `innovation_story_strength`, and `source_support_strength`, while penalizing `implementation_risk`, `eval_risk`, `estimated_runtime_cost`, `patch_surface`, `dependency_drag`, and `baseline_distance`.

## Campaign Inputs

- `research_campaign` is the preferred input for the third scenario.
- It should include:
  - `current_research`
  - `task_family`
  - `dataset`
  - `benchmark`
  - `evaluation_source`
  - `sota_reference`
- `candidate_ideas`
- `compute_budget`
- `research_lookup`
- `idea_policy`
- `source_constraints`
- `feasibility_policy`
- `baseline_gate`
- `execution_policy`
- `variant_spec`
- Treat user-provided `evaluation_source` and `sota_reference` as frozen inputs for this campaign; do not claim they are globally complete.

## Variant Spec Hints

- Use `current_research` to anchor the exploratory context.
- Use `variant_axes`, `subset_sizes`, and `short_run_steps` to describe the candidate matrix.
- Use `selection_weights` to tune the pre-execution balance between `cost`, `success_rate`, and `expected_gain`.
- Use `primary_metric` and `metric_goal` to control post-execution candidate ranking.

## Boundaries

- This skill owns end-to-end exploratory orchestration on top of `current_research`.
- This skill is intentionally narrow: it governs implementation, execution, and comparison after the researcher has already constrained the task.
- Keep narrow code-only asks on `explore-code`.
- Keep narrow run-only asks on `explore-run`.
- Do not require any skill outside this repository.
- Do not promise automatic benchmark completeness, novelty proof, or final human-verified SOTA claims.
- Treat lookup evidence as layered: `external_provider` is strongest, `parsed_locator` and `repo_local_extracted` are weaker support, and `seed_only` must not be treated as strong research evidence.

## Notes

Use `references/research-explore-policy.md`, `references/research-campaign-spec.md`, `../../references/explore-variant-spec.md`, `scripts/orchestrate_explore.py`, and `scripts/write_outputs.py`.
