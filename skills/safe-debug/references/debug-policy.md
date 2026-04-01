# Debug Policy

## Default protocol

1. read the error or symptom carefully
2. diagnose without editing repository code
3. state the likely cause, evidence, and smallest safe fix
4. require explicit approval before patching

## Required outputs

- diagnosis summary
- likely cause category
- conservative fix suggestions
- savepoint recommendation when change scope is medium or high

## Forbidden behavior

- editing code before approval
- drifting into broad refactor work
- silently routing into exploration
