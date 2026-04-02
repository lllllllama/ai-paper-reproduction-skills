---
name: research-explore
description: Explore-lane end-to-end orchestrator for deep learning research repositories. Use when the researcher explicitly authorizes candidate-only exploration on top of `current_research`, and the task spans isolated code adaptation plus exploratory run planning or candidate ranking, with outputs written to `explore_outputs/`. Do not use for README-first trusted reproduction, narrow code-only or run-only exploration, passive repo analysis, or implicit experimentation.
---

# research-explore

## Workflow

- Confirm `current_research` in a durable form such as a branch, commit, checkpoint, run record, or already-trained local model state.
- Keep all exploration on an isolated experiment branch or worktree.
- Use `analyze-project` only when insertion points, entrypoints, or config relationships are still unclear.
- Use `env-and-assets-bootstrap` only when the environment or assets tied to `current_research` are still unclear.
- Use `explore-code` for bounded exploratory code adaptation.
- Use `explore-run` for short-cycle trials, sweeps, and candidate ranking.
- Let execution hand off to `minimal-run-and-audit` or `run-train` only when the exploratory plan needs real command execution.
- Write candidate-only outputs to `explore_outputs/`; never present the result as trusted reproduction success.

## Boundaries

- This skill owns end-to-end exploratory orchestration on top of `current_research`.
- Keep narrow code-only asks on `explore-code`.
- Keep narrow run-only asks on `explore-run`.
- Do not require any skill outside this repository.

## Notes

Use `references/research-explore-policy.md`, `scripts/orchestrate_explore.py`, and `scripts/write_outputs.py`.
