# Example Prompt: Sub-skills

## repo-intake-and-plan

Scan this repository with `repo-intake-and-plan`.

- read the README first
- inspect common files like `requirements.txt`, `environment.yml`, `pyproject.toml`, `setup.py`, `configs/`, `scripts/`, `tools/`, and `Dockerfile`
- extract documented commands
- classify them into inference, evaluation, training, or other
- recommend the minimum trustworthy reproduction target
- do not run anything yet

## env-and-assets-bootstrap

Use `env-and-assets-bootstrap` for this repository.

- prefer conda-style setup
- use README-documented asset paths first
- prepare a conservative dataset, checkpoint, and cache plan
- record unresolved dependency or asset risks
- do not choose a new reproduction target on your own

## minimal-run-and-audit

Use `minimal-run-and-audit`.

- run the selected smoke or documented command
- keep reporting concise
- write `SUMMARY.md`, `COMMANDS.md`, `LOG.md`, and `status.json`
- write `PATCHES.md` only if repository files changed
- label commands as documented, adapted, or inferred

## paper-context-resolver

Use `paper-context-resolver` only if README and repository files leave a reproduction-critical gap.

- prefer the README-linked paper
- otherwise use arXiv, OpenReview, or official project sources
- only answer reproduction-relevant questions
- record conflicts instead of silently replacing README guidance
- do not use it for general paper summaries or title-only lookup
