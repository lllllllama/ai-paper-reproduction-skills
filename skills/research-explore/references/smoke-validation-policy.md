# Smoke Validation Policy

`research-explore` should prefer cheap, auditable smoke checks before broader exploratory execution.

## Required Checks

- syntax parse for candidate Python files
- import-resolution style sanity for touched modules
- config path resolution for frozen commands
- constructor surface availability
- forward surface availability
- short-run command verification or explicit planned state

## Reporting

- write a standardized `TRANSPLANT_SMOKE_REPORT.md`
- record per-check status and blockers
- distinguish `planned` from `passed` and `failed`

## Guardrails

- smoke success does not imply trusted correctness
- smoke success does not imply global benchmark validity
- smoke failure should block broader candidate execution when the blocker is structural
