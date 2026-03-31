# ai-paper-reproduction-skills

Codex multi-skill repository for README-first AI paper repository reproduction.

The main skill is `ai-paper-reproduction`. Most users should start there.

Use this repository when you want Codex to reproduce an AI paper repo by reading the README first, choosing the smallest trustworthy documented target, and writing standardized outputs.

## What it optimizes for

- `README-first`
- `inference/eval first`
- `minimal trustworthy changes`
- `auditable patching`

## Quick Start

Install all 5 skills with the `skills` CLI:

```bash
npx skills add lllllllama/ai-paper-reproduction-skills --all
```

Then start with the main skill:

```text
Use ai-paper-reproduction on this AI repo. Stay README-first, prefer documented inference or evaluation, avoid unnecessary repo changes, and write outputs to repro_outputs/.
```

Installation note:

- Default install for this repository:

```bash
npx skills add lllllllama/ai-paper-reproduction-skills --all
```

- If you only want the main skill:

```bash
npx skills add lllllllama/ai-paper-reproduction-skills --skill ai-paper-reproduction
```

- The repository keeps one `SKILL.md` per skill under `skills/`, so it is compatible with multi-skill GitHub repository discovery in the `skills` CLI.

## Skills included

- `ai-paper-reproduction`
  - orchestrates README-first reproduction from intake through reporting
- `repo-intake-and-plan`
  - maps the repo, extracts documented commands, and recommends the smallest credible target
- `env-and-assets-bootstrap`
  - prepares conservative environment, checkpoint, dataset, and cache assumptions before execution
- `minimal-run-and-audit`
  - captures execution evidence and writes standardized `repro_outputs/`
- `paper-context-resolver`
  - resolves a narrow paper-critical gap only when README and repo evidence are insufficient

## Output files

- `SUMMARY.md`
  - first page result and main blocker
- `COMMANDS.md`
  - copyable setup, asset, run, and verification commands
- `LOG.md`
  - concise process record with evidence and decisions
- `status.json`
  - stable machine-readable status
- `PATCHES.md`
  - patch record, only when repository files were modified

## Language behavior

- Human-readable outputs may follow the user's language.
- Machine-readable fields in `status.json` stay in English.
- Filenames stay in English.
- Commands, paths, package names, and config keys stay unchanged.

## Examples

- Main skill examples: [examples/example_prompt_main.md](examples/example_prompt_main.md)
- Sub-skill examples: [examples/example_prompt_subskills.md](examples/example_prompt_subskills.md)
- Real repo trials: [examples/real_repo_trials.md](examples/real_repo_trials.md)
- Release notes: [CHANGELOG.md](CHANGELOG.md)

## Current scope

- README-first reproduction of AI paper repositories
- documented inference or evaluation first
- training only as startup or partial verification unless explicitly needed
- explicit blockers instead of silent semantic changes

## Not a general research mega-skill

This repository is not a general paper summarizer, benchmark design toolkit, or experiment platform.
