---
name: safe-debug
description: Trusted-lane debug skill for deep learning research work. Use when the user pastes a traceback, terminal error, CUDA OOM, checkpoint load failure, shape mismatch, NaN loss symptom, or training failure and wants conservative diagnosis before any patching. Do not use for broad refactoring, speculative adaptation, automatic exploratory patching, or general repository familiarization.
---

# safe-debug

## When to apply

- The user provides a traceback, terminal error, or concrete training or inference failure symptom.
- The user wants diagnosis, root-cause narrowing, and minimal patch suggestions before code is changed.
- The user wants a safe debug flow with explicit human approval before mutation.

## When not to apply

- When the user wants a broad repository walkthrough without an active failure.
- When the task is speculative experimentation or code adaptation.
- When the user is asking for a large refactor or readability rewrite.

## Clear boundaries

- Diagnose first.
- Do not modify repository code by default.
- If a patch is needed, propose the smallest fix and require explicit approval first.
- Escalate savepoint or branch creation before medium-risk or high-risk changes.

## Output expectations

- `debug_outputs/DIAGNOSIS.md`
- `debug_outputs/PATCH_PLAN.md`
- `debug_outputs/status.json`

## Notes

Use `references/debug-policy.md` and the shared `references/research-pitfall-checklist.md`.
