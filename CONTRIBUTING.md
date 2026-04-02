# Contributing

Keep changes small, lane-aware, and easy to validate.

## Local workflow

1. Edit the relevant files under `skills/`, `references/`, `shared/`, or `scripts/`.
2. Run the full validation set:

```bash
python scripts/validate_repo.py
python scripts/test_bootstrap_env.py
python scripts/test_install_targets.py
python scripts/test_skill_registry.py
python scripts/test_trigger_boundaries.py
python scripts/test_readme_selection.py
python scripts/test_output_rendering.py
python scripts/test_train_output_rendering.py
python scripts/test_analysis_output_rendering.py
python scripts/test_safe_debug_output_rendering.py
python scripts/test_explore_output_rendering.py
python scripts/test_explore_variant_matrix.py
python scripts/test_setup_planning.py
python scripts/test_orchestrator_dry_run.py
python scripts/test_training_lane_routing.py
```

3. If installation behavior changed, also run:

```bash
python scripts/install_skills.py --client codex --target ./tmp/codex-skills --force
python scripts/install_skills.py --client claude --target ./tmp/claude-skills --force
```

4. Commit only after the repository validates cleanly.

## Repository rules

- Keep every skill folder named exactly after its front matter `name`.
- Register every public or helper skill in `references/skill-registry.json`.
- Keep `SKILL.md` focused on boundaries and workflow.
- Put detailed policy in `references/`.
- Put reusable writers and shared helpers in `shared/`.
- Keep helper skills narrow.
- Preserve trusted-lane defaults unless the change intentionally introduces or updates an explore-lane capability.

## Lane rules

- Trusted skills must not auto-route into exploration.
- Explore skills require explicit authorization signals.
- Helper skills should usually be orchestrator-invoked.
- Same-level skills should not call each other directly.
- Exploratory outputs must not be represented as trusted baseline results.

## Output compatibility

- Machine-readable keys and enums stay in stable English.
- Existing `repro_outputs/` behavior must remain backward compatible unless a migration is documented.
- New output directories should extend the contract, not silently replace existing trusted bundles.

## Pull request checklist

- `python scripts/validate_repo.py` passes
- `python scripts/test_skill_registry.py` passes
- `python scripts/test_trigger_boundaries.py` passes
- `python scripts/test_readme_selection.py` passes
- all lane-specific rendering tests pass
- installer and bootstrapper checks pass for both Codex and Claude Code entrypoints
- orchestrator dry-run still reflects the intended trusted chain
- helper/public/explore metadata still matches the actual boundaries
- output contract changes are intentional and documented
