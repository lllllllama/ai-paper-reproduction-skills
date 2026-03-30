# ai-paper-reproduction-skill

`ai-paper-reproduction-skill` is a Codex multi-skill repository for README-first AI paper reproduction.

It is organized as:

- one main skill for end-to-end orchestration
- multiple sub-skills for intake, setup, execution, and optional paper-gap resolution

## What it optimizes for

- `README-first`
- `inference/eval first`
- `minimal trustworthy changes`
- `auditable patching`

## Quick Start

Install the skills into your Codex skills directory:

```bash
python scripts/install_skills.py --force
```

Then use the main skill on a target AI repository:

```text
Use ai-paper-reproduction on this AI paper repository. Stay README-first, prefer documented inference or evaluation, avoid unnecessary repo changes, and write outputs to repro_outputs/.
```

## Usage example

Use `ai-paper-reproduction` on this AI paper repository. Stay README-first, choose the smallest trustworthy documented inference or evaluation target, avoid unnecessary code changes, and write outputs to `repro_outputs/`.

Chinese example:

使用 `ai-paper-reproduction` 复现这个 AI 仓库。先读 README，优先选择已文档化的 inference 或 evaluation，尽量不要修改仓库代码，并把输出写到 `repro_outputs/`。

## Skills

### Main skill

- `ai-paper-reproduction`
  - reads the repo README first
  - selects the minimum trustworthy target
  - coordinates the sub-skills
  - normalizes outputs and patch handling

### Sub-skills

- `repo-intake-and-plan`
  - scans the repo and extracts documented commands
- `env-and-assets-bootstrap`
  - prepares conservative environment and asset assumptions
- `minimal-run-and-audit`
  - normalizes execution evidence and writes standardized outputs
- `paper-context-resolver`
  - optionally fills a narrow reproduction-critical gap from the paper

## Output files

All human-readable outputs go to `repro_outputs/`.

- `SUMMARY.md`
  - first-page result, main blocker, and patch status when relevant
- `COMMANDS.md`
  - copyable setup, asset, run, and verification commands
- `LOG.md`
  - concise process record with evidence and decisions
- `status.json`
  - stable machine-readable status
- `PATCHES.md`
  - patch record, only when repository files were modified

## Release checks

For maintainers and release validation:

```bash
python scripts/validate_repo.py
python scripts/test_trigger_boundaries.py
python scripts/test_readme_selection.py
python scripts/test_output_rendering.py
```

## Current scope

- README-first reproduction of AI paper repositories
- prefer documented inference or evaluation
- treat training as startup or partial verification unless full training is explicitly needed
- record blockers instead of silently changing repository semantics

## Not a general research mega-skill

This repository is not meant to be a general research assistant, paper summarizer, or experiment platform.

It stays narrow on purpose:

- README-first repo reproduction
- low-risk changes
- explicit outputs
- patch auditability
