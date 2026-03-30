# Contributing

This repository is a Codex multi-skill collection. Keep changes small, readable, and easy to validate.

## Local workflow

1. Edit the relevant files under `skills/`.
2. Run:

```bash
python scripts/validate_repo.py
```

3. If you changed installation behavior, also test:

```bash
python scripts/install_skills.py --target ./tmp/skills --force
```

4. Commit only after the repository validates cleanly.

## Repository rules

- Keep each skill folder named exactly after its front matter `name`.
- Keep `SKILL.md` focused on workflow and boundaries.
- Move detailed policy into `references/`.
- Keep reusable output templates in `assets/`.
- Keep helper automation in `scripts/`.
- Avoid heavy runtime dependencies.
- Preserve the README-first reproduction scope.

## Compatibility rules

- Human-readable Markdown may adapt to user language.
- Machine-readable keys and enums must remain in stable English.
- Output filenames under `repro_outputs/` must remain stable unless there is a strong migration reason.

## Pull request checklist

- `python scripts/validate_repo.py` passes
- installer still works
- changed skill metadata still matches its folder and purpose
- output spec changes are intentional and documented
