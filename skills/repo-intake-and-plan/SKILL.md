---
name: repo-intake-and-plan
description: Sub-skill for the intake phase of README-first AI repo reproduction. Use when the task is specifically to scan a repository, read README and common project files, extract documented commands, classify inference or evaluation or training candidates, and return a minimum trustworthy plan to the main skill. Do not use for environment setup, asset download, command execution, final reporting, paper lookup, or end-to-end orchestration.
---

# repo-intake-and-plan

## When to apply

- At the beginning of README-first reproduction work.
- When the main skill needs a fast map of repo structure and documented commands.
- When inference, evaluation, and training candidates must be classified conservatively.
- When the user explicitly wants to inspect the repo first and not run anything yet.

## When not to apply

- When execution has already started and the task is now about running commands or writing outputs.
- When the target is not a repository-backed reproduction task.
- When the user only wants paper interpretation without repo inspection.
- When the user already has a selected documented command and only needs setup or execution.

## Clear boundaries

- This skill scans and plans.
- It does not install environments.
- It does not prepare large assets.
- It does not execute substantive reproduction commands.
- It does not decide high-risk patching.

## Input expectations

- Target repository path.
- Access to README and common project files if present.
- Optional user hints about desired priority, such as inference-first.

## Output expectations

- concise repo structure summary
- documented command inventory
- inferred candidate categories: inference, evaluation, training, other
- minimum trustworthy reproduction recommendation
- notable ambiguity or risk list

## Notes

Use `references/repo-scan-rules.md` and helper scripts under `scripts/`.
