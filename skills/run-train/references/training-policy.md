# Training Policy

## Purpose

Use this skill for trusted-lane training execution after a training command has already been selected.

## Requirements

- state whether the run is startup verification, short-run verification, full kickoff, or resume
- record the exact training command
- record dataset and checkpoint assumptions explicitly
- separate blocked, partial, resumed, and verified states
- record `max_steps`, `completed_steps`, `best_metric`, `best_checkpoint`, and `stop_reason` when available
- keep conclusions conservative when the run is short or partial

## Avoid

- exploratory sweeps
- speculative architecture changes
- implying that startup verification equals full reproduction success
