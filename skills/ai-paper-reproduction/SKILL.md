---
name: ai-paper-reproduction
description: Main orchestration skill for README-first reproduction of AI paper repositories. Use when the user wants an end-to-end minimal trustworthy reproduction flow that reads the repo, selects the smallest documented inference or evaluation target, coordinates the intake, setup, execution, and optional paper-gap sub-skills, enforces conservative patch rules, and writes the standardized `repro_outputs/` bundle. Do not use for paper summary, generic environment setup, isolated repo scanning, standalone command execution, or broad research assistance outside repository-grounded reproduction.
---

# ai-paper-reproduction

## Use when

- The user wants Codex to reproduce an AI paper repository.
- The target is a code repository with a README, scripts, configs, or documented commands.
- The goal is a minimal trustworthy run, not unlimited experimentation.
- The user needs standardized outputs that another human or model can audit quickly.
- The task spans more than one stage, such as intake plus setup, or setup plus execution plus reporting.

## Do not use when

- The task is a general literature review or paper summary.
- The task is to design a new model, benchmark suite, or training pipeline from scratch.
- The repository is not centered on AI or does not expose a documented reproduction path.
- The user primarily wants a deep code refactor rather than README-first reproduction.
- The user is explicitly asking for only one narrow phase that a sub-skill already covers cleanly.

## Success criteria

- README is treated as the primary source of reproduction intent.
- A minimum trustworthy target is selected and justified.
- Documented inference is preferred over evaluation, and evaluation is preferred over training.
- Any repo edits remain conservative, explicit, and auditable.
- `repro_outputs/` is generated with consistent structure and stable machine-readable fields.
- Final user-facing explanation is short and follows the user's language when practical.

## Interaction and usability policy

- Keep the workflow simple enough for a new user to understand quickly.
- Prefer short, concrete plans over exhaustive research.
- Expose commands, assumptions, blockers, and evidence.
- Avoid turning the skill into an opaque automation layer.
- Preserve a low learning cost for both humans and downstream agents.

## Language policy

- Human-readable Markdown outputs should follow the user's language when it is clear.
- If the user's language is unclear, default to concise English.
- Machine-readable fields, filenames, keys, and enum values stay in stable English.
- Paths, package names, CLI commands, config keys, and code identifiers remain unchanged.

See `references/language-policy.md`.

## Reproduction policy

Core priority order:

1. documented inference
2. documented evaluation
3. documented training startup or partial verification
4. full training only when the user explicitly asks later

Rules:

- README-first: use repository files to clarify, not casually override, the README.
- Aim for minimal trustworthy reproduction rather than maximum task coverage.
- Treat smoke tests, startup verification, and early-step checks as valid training evidence when full training is not appropriate.
- Record unresolved gaps rather than fabricating confidence.

## Patch policy

- Prefer no code changes.
- Prefer safer adjustments first:
  - command-line arguments
  - environment variables
  - path fixes
  - dependency version fixes
  - dependency file fixes such as `requirements.txt` or `environment.yml`
- Avoid changing:
  - model architecture
  - core inference semantics
  - core training logic
  - loss functions
  - experiment meaning
- If repository files must change:
  - create a patch branch first using `repro/YYYY-MM-DD-short-task`
  - apply low-risk changes before medium-risk changes
  - avoid high-risk changes by default
  - commit only verified groups of changes
  - keep verified patch commits sparse, usually `0-2`
  - use commit messages in the form `repro: <scope> for documented <command>`

See `references/patch-policy.md`.

## Workflow

1. Read README and repo signals.
2. Call `repo-intake-and-plan` to scan the repository and extract documented commands.
3. Select the smallest trustworthy reproduction target.
4. Call `env-and-assets-bootstrap` to prepare environment assumptions and asset paths.
5. Run a conservative smoke check or documented command with `minimal-run-and-audit`.
6. Use `paper-context-resolver` only if README and repo files leave a narrow reproduction-critical gap that blocks the current target.
7. Write the standardized outputs.
8. Give the user a short final note in the user's language.

## Required outputs

Always target:

```text
repro_outputs/
  SUMMARY.md
  COMMANDS.md
  LOG.md
  status.json
  PATCHES.md   # only if patches were applied
```

Use the templates under `assets/` and the field rules in `references/output-spec.md`.

## Reporting policy

- Put the shortest high-value summary in `SUMMARY.md`.
- Put copyable commands in `COMMANDS.md`.
- Put process evidence, assumptions, failures, and decisions in `LOG.md`.
- Put durable machine-readable state in `status.json`.
- Put branch, commit, validation, and README-fidelity impact in `PATCHES.md` when needed.
- Distinguish verified facts from inferred guesses.

## Maintainability notes

- Keep this skill narrow: README-first AI repo reproduction only.
- Push specialized logic into sub-skills or helper scripts.
- Prefer stable templates and simple schemas over ad hoc prose.
- Keep machine-readable outputs backward compatible when possible.
- Add new evidence sources only when they improve auditability without raising learning cost.
