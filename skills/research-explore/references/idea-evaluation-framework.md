# Idea Evaluation Framework

`research-explore` uses a bounded, candidate-only evaluation scheme for third-scenario idea ranking.

## Hard Gates

- baseline gate must not be `abandon`
- `single_variable_fit >= 0.6`
- `interface_fit >= 0.5`
- `patch_surface <= 0.7`
- `dependency_drag <= 0.7`
- `eval_risk <= 0.6`
- `short_run_feasibility != blocked`

## Soft Ranking

Positive contributions:

- `expected_upside`
- `single_variable_fit`
- `interface_fit`
- `rollback_ease`
- `innovation_story_strength`
- `source_support_strength`
- `execution_feasibility`

Negative contributions:

- `implementation_risk`
- `eval_risk`
- `patch_surface`
- `dependency_drag`
- `execution_cost`
- `baseline_distance`

## Provenance

Each ranked card should record where each field came from:

- campaign input
- read-only repo analysis
- source lookup cache
- source mapping and patch planning
- execution feasibility or smoke evidence

## Guardrails

- ranking is for candidate prioritization only
- ranking does not prove novelty
- ranking does not prove benchmark completeness
- ranking does not prove verified SOTA superiority
