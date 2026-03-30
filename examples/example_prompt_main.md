# Example Prompt: Main Skill

Use `ai-paper-reproduction` on this AI paper repository.

Requirements:

- stay README-first
- choose the smallest trustworthy documented target
- prefer documented inference, then documented evaluation, then training startup only if needed
- avoid repo code changes unless clearly necessary
- if patches are needed, keep them conservative and auditable
- write outputs to `repro_outputs/`
- keep human-readable outputs in my language, but keep `status.json` keys in English
- use `paper-context-resolver` only if a concrete reproduction gap remains after README and repo inspection

At the end, give me:

- a short result summary
- the selected documented command
- any blocker
- the generated output files

Short version:

> Reproduce this AI repo with `ai-paper-reproduction`. Stay README-first, prefer documented inference or evaluation, avoid unnecessary repo edits, and write audited outputs to `repro_outputs/`.
