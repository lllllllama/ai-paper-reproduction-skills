# Output Contract

This repository maintains two output styles.

## Trusted outputs

Trusted-lane outputs should be audit-heavy and durable.

Expected directories include:

- `repro_outputs/`
- `analysis_outputs/`
- `debug_outputs/`
- `train_outputs/`

Trusted output traits:

- stable machine-readable English keys
- concise human-readable summaries
- assumptions, deviations, and blockers recorded explicitly
- next safe action recorded when work is partial or blocked

## Explore outputs

Explore-lane outputs should be summary-heavy and disposable.

Expected directories include:

- `explore_outputs/`

Explore output traits:

- `current_research` recorded as the exploratory anchor
- canonical `explore_context` recorded with `current_research`, `experiment_branch`, and explicit authorization
- helper stage trace recorded for the orchestration path that produced the bundle
- raw/pruned variant counts, budget caps, and best runs summarized
- pre-execution selection policy recorded when exploratory candidates are ranked before execution
- metric policy for candidate ranking recorded when explicit exploratory ranking is configured
- source references for transplanted or adapted modules recorded
- enough context for a human to decide whether to continue
- no implicit claim that exploratory gains are trusted baselines
- isolated branch or worktree context recorded

## Compatibility

- Existing trusted `repro_outputs/` remain stable.
- New lanes may add new output directories, but should not silently change established trusted schemas.
