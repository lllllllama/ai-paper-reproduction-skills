# ai-paper-reproduction-skill

`ai-paper-reproduction-skill` is a Codex multi-skill repository for README-first AI repository reproduction.

It is not a generic research toolbox. It is a focused skill set for:

- reading the target repository README first
- selecting the smallest trustworthy reproduction target
- favoring documented inference or evaluation over large training jobs
- recording any repo patches in an auditable way
- producing a stable output bundle for both humans and downstream AI tools

## Skills

### Main skill

- `ai-paper-reproduction`
  - Orchestrates README-first reproduction.
  - Chooses the minimum trustworthy target.
  - Normalizes reporting, patch rules, and user-facing output.

### Sub-skills

- `repo-intake-and-plan`
  - Scans the target repo and extracts documented commands.
  - Identifies inference, evaluation, and training candidates.
  - Proposes the minimum credible plan to the main skill.

- `env-and-assets-bootstrap`
  - Prepares a conservative environment and common asset layout.
  - Prefers conda or Anaconda-style setup.
  - Resolves checkpoints, datasets, and caches from README-first evidence.

- `minimal-run-and-audit`
  - Runs smoke checks or documented commands.
  - Writes standardized outputs in `repro_outputs/`.
  - Records verified patch information when repo files changed.

- `paper-context-resolver`
  - Optional enhancement module.
  - Helps resolve missing reproduction details from primary paper sources.
  - Does not replace README instructions by default.

## Design principles

- README-first
- minimal trustworthy reproduction
- inference or evaluation first
- auditable patching
- optional paper-assisted reproduction
- low learning cost

## Quick start

1. Clone this repository.
2. Install the skills into your Codex skills directory.
3. Validate the local repository after changes.
4. Point Codex at a target AI paper repository.
5. Use the main skill request pattern below.
6. Review the generated `repro_outputs/` bundle.

Example natural-language request:

> Reproduce this repository with the `ai-paper-reproduction` skill. Stay README-first, aim for the smallest trustworthy documented inference or evaluation run, and write outputs to `repro_outputs/`.

## Install to Codex

Default target:

- Windows: `%USERPROFILE%\\.codex\\skills`
- macOS or Linux: `${HOME}/.codex/skills`
- If `CODEX_HOME` is set, the installer uses `${CODEX_HOME}/skills`

Install by copying the skill folders:

```bash
python scripts/install_skills.py --force
```

Install to a custom skills directory:

```bash
python scripts/install_skills.py --target /path/to/skills --force
```

Install by symlink instead of copy:

```bash
python scripts/install_skills.py --mode symlink --force
```

Validate the repository before or after publishing:

```bash
python scripts/validate_repo.py
```

This repository is intentionally lightweight:

- Markdown files describe the skill behavior.
- Small Python and shell scripts provide optional scaffolding.
- No heavy framework is required to understand or extend it.

If you want to adapt it:

- edit the skill policies under `skills/*/references/`
- adjust templates under `skills/ai-paper-reproduction/assets/`
- extend the helper scripts under `skills/*/scripts/`
- run `python scripts/validate_repo.py` before committing

## Maintenance

This repository is maintained as a skill collection, not as a Python application.

Practical maintenance rules:

- keep front matter names aligned with folder names
- keep `SKILL.md` concise and move detailed rules into `references/`
- keep reusable templates in `assets/`
- keep deterministic logic in `scripts/`
- preserve stable English machine-readable fields in `status.json`
- prefer backward-compatible output changes

For contributor workflow and repository checks, see `CONTRIBUTING.md`.

## Output bundle

The standardized output directory is:

```text
repro_outputs/
  SUMMARY.md
  COMMANDS.md
  LOG.md
  status.json
  PATCHES.md   # only when repository files were modified
```

Purpose of each file:

- `SUMMARY.md`: first page for humans
- `COMMANDS.md`: copyable commands
- `LOG.md`: concise process record
- `status.json`: stable machine-readable status
- `PATCHES.md`: auditable patch history and verification notes

## Scope guardrails

This repository stays focused on README-first AI repo reproduction.

It does not try to:

- become a full experiment platform
- silently rewrite project semantics
- default to full training
- replace primary repository documentation with paper summaries

## Optional paper assistance

`paper-context-resolver` is optional. Use it only when README and repo files leave a reproduction-critical gap. When README and paper disagree, record the conflict instead of silently replacing README guidance.

## Repository layout

```text
ai-paper-reproduction-skill/
  README.md
  CONTRIBUTING.md
  .gitignore
  .editorconfig
  .github/workflows/validate.yml
  scripts/
    install_skills.py
    validate_repo.py
  skills/
    ai-paper-reproduction/
    repo-intake-and-plan/
    env-and-assets-bootstrap/
    minimal-run-and-audit/
    paper-context-resolver/
  examples/
```
