---
name: explore-code
description: Explore-lane code adaptation skill for deep learning research repositories. Use when the researcher explicitly authorizes exploratory work on an isolated branch or worktree to transplant modules, adapt a backbone, add LoRA or adapter layers, replace a head, or stitch together low-risk migration ideas with summary-only records in `explore_outputs/`. Do not use for trusted baseline reproduction, conservative debugging, environment setup, or default repository analysis.
---

# explore-code

## When to apply

- When the researcher explicitly authorizes exploratory code changes on an isolated branch or worktree.
- When the task is source-anchored module transplant, backbone adaptation, LoRA or adapter insertion, or low-risk module combination.
- When summary-level recording is sufficient and the result is a candidate, not a trusted conclusion.

## When not to apply

- When the request is for trusted baseline work, conservative debugging, or normal training execution.
- When the user did not explicitly authorize exploratory modifications.
- When the task is a broad refactor or a from-scratch idea implementation.

## Clear boundaries

- This skill owns exploratory code modifications only.
- It must keep work isolated from the trusted baseline.
- It may hand off execution to `minimal-run-and-audit` or `run-train`.
- It should favor source-anchored copying and minimal adaptation over freeform rewrites.

## Output expectations

- `explore_outputs/CHANGESET.md`
- `explore_outputs/TOP_RUNS.md`
- `explore_outputs/status.json`

## Notes

Use `references/explore-policy.md` and `scripts/write_outputs.py`.
