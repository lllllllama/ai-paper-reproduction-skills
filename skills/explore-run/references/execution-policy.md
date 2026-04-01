# Explore Run Policy

## Purpose

Use this skill only when exploratory execution has been explicitly authorized.

## Requirements

- keep experiment runs isolated from the trusted baseline
- prefer small-subset or short-cycle checks before heavier exploratory runs
- record baseline ref, experiment branch, variant count, and top runs
- summarize candidates for human review instead of claiming trusted success

## Avoid

- default or implicit exploration
- rewriting training logic inside this skill
- promoting exploratory results into the trusted lane automatically
