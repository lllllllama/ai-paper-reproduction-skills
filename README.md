# ai-paper-reproduction-skills

Codex multi-skill repository for deep learning research workflows with a trusted-lane default.

The repository now ships a trusted lane, an explore lane, and two helper skills. Existing public skill names remain unchanged for compatibility.

## Core policy

- trusted by default
- README-first for reproduction
- explicit exploration only
- low-risk changes before code edits
- audit-heavy trusted outputs
- summary-heavy exploratory outputs

Shared routing, branch, pitfall, and output rules live under [references/](references/).

## Install

Install the full repository skill set:

```bash
npx skills add lllllllama/ai-paper-reproduction-skills --all
```

Install only the main orchestrator:

```bash
npx skills add lllllllama/ai-paper-reproduction-skills --skill ai-paper-reproduction
```

## Trusted lane

- `ai-paper-reproduction`
  - end-to-end README-first reproduction orchestrator
- `env-and-assets-bootstrap`
  - conservative environment, checkpoint, dataset, and cache planning
- `minimal-run-and-audit`
  - inference, evaluation, smoke, and sanity execution with `repro_outputs/`
- `analyze-project`
  - read-only repository and model analysis with `analysis_outputs/`
- `run-train`
  - trusted training execution with `train_outputs/`
- `safe-debug`
  - conservative research debugging with `debug_outputs/`

## Explore lane

- `explore-code`
  - isolated exploratory code adaptation and transplant work with `explore_outputs/`
- `explore-run`
  - isolated exploratory run planning, sweeps, and ranking with `explore_outputs/`

## Helper skills

- `repo-intake-and-plan`
  - narrow helper for repo scanning and documented command extraction
- `paper-context-resolver`
  - narrow helper for README-paper gap resolution

These helper skills are usually orchestrator-invoked rather than primary user entrypoints.

## How to use

Trusted reproduction:

```text
Use ai-paper-reproduction on this AI repo. Stay README-first, prefer documented inference or evaluation, avoid unnecessary repo changes, and write outputs to repro_outputs/.
```

Read-only project analysis:

```text
Use analyze-project on this repo. Read the code, map the model and training entrypoints, and flag suspicious patterns without editing files.
```

Trusted training:

```text
Use run-train on this repo. Run the selected documented training command conservatively for startup verification and write train_outputs/.
```

Safe debug:

```text
Use safe-debug on this traceback. Diagnose the failure first, propose the smallest safe fix, and do not patch until I approve.
```

Explicit exploration:

```text
Use explore-code on an isolated branch. Try a LoRA adaptation for this backbone, keep it exploratory only, and summarize the changes in explore_outputs/.
```

```text
Use explore-run on an experiment branch. Do a small-subset short-cycle sweep, rank the top runs, and treat the results as candidates only.
```

## Output directories

- `repro_outputs/`
  - trusted reproduction bundle
- `analysis_outputs/`
  - read-only project analysis
- `debug_outputs/`
  - trusted debug diagnosis and patch plan
- `train_outputs/`
  - trusted training execution bundle
- `explore_outputs/`
  - exploratory changeset and run ranking

## Routing summary

- ambiguous requests go to the trusted lane
- exploration requires explicit authorization
- trusted skills must not auto-route into exploration
- explore skills must not claim trusted reproduction success
- same-level skills should not call each other directly

## Registry and policies

- Skill registry: [references/skill-registry.json](references/skill-registry.json)
- Routing policy: [references/routing-policy.md](references/routing-policy.md)
- Branch and commit policy: [references/branch-and-commit-policy.md](references/branch-and-commit-policy.md)
- Output contract: [references/output-contract.md](references/output-contract.md)
- Research pitfall checklist: [references/research-pitfall-checklist.md](references/research-pitfall-checklist.md)

## Scope

This repository is not a general paper summarizer or an unconstrained autonomous research agent. It is a lane-aware deep learning research toolkit that optimizes for safety, observability, and reuse.
