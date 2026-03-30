# ai-paper-reproduction-skill

Multi-skill repository for README-first AI paper repository reproduction.

The main skill is `ai-paper-reproduction`. Most users should start there.

Use this repository when you want Codex to reproduce an AI paper repo by reading the README first, choosing the smallest trustworthy documented target, and writing standardized outputs.

## What it optimizes for

- `README-first`
- `inference/eval first`
- `minimal trustworthy changes`
- `auditable patching`

## Quick Start

Install the skills:

```bash
python scripts/install_skills.py --force
```

Then start with the main skill:

```text
Use ai-paper-reproduction on this AI repo. Stay README-first, prefer documented inference or evaluation, avoid unnecessary repo changes, and write outputs to repro_outputs/.
```

Installation note:

- The repository keeps one `SKILL.md` per skill under `skills/`, so it works as a public multi-skill GitHub repository and can also be copied or symlinked into a local skills directory.

## Skills included

- `ai-paper-reproduction`
  - main README-first orchestrator for minimal trustworthy AI repo reproduction
- `repo-intake-and-plan`
  - scans the repo and extracts documented commands and candidate paths
- `env-and-assets-bootstrap`
  - prepares conservative environment and asset assumptions before execution
- `minimal-run-and-audit`
  - normalizes execution evidence and writes `repro_outputs/`
- `paper-context-resolver`
  - optionally resolves a narrow paper-related reproduction gap

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
