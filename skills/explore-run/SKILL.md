---
name: explore-run
description: Explore-lane experimental execution skill for deep learning research repositories. Use when the researcher explicitly authorizes exploratory runs such as small-subset validation, short-cycle guess-and-check, batch sweeps, idle-GPU search, or quick transfer-learning trials, with results summarized in `explore_outputs/`. Do not use for trusted baseline execution, conservative training verification, default routing, or implicit experimentation.
---

# explore-run

## When to apply

- When the researcher explicitly authorizes exploratory runs.
- When the task is a small-subset validation, short-cycle training probe, batch sweep, idle-GPU search, or quick transfer-learning trial.
- When the output should rank candidate runs rather than certify trusted success.

## When not to apply

- When the user wants trusted training execution or conservative verification.
- When there is no explicit exploratory authorization.
- When the task is repository setup, intake, or debugging.

## Clear boundaries

- This skill owns exploratory execution planning and summary only.
- It may hand off actual command execution to `minimal-run-and-audit` or `run-train`.
- It should keep experiment state isolated from the trusted baseline.
- It should prefer small-subset and short-cycle checks before heavier exploratory runs.

## Output expectations

- `explore_outputs/CHANGESET.md`
- `explore_outputs/TOP_RUNS.md`
- `explore_outputs/status.json`

## Notes

Use `references/execution-policy.md`, `scripts/plan_variants.py`, and `scripts/write_outputs.py`.
