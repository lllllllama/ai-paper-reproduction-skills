# Output Spec

All runs should target the same output directory:

```text
repro_outputs/
```

When the selected trustworthy target is documented training, the orchestrator may also emit a supplemental:

```text
train_outputs/
```

That training bundle should hold the training-specific checkpoint, metric, and monitoring state, while `repro_outputs/` remains the primary reproduction-facing summary.

## `SUMMARY.md`

Audience:

- first human reader
- another model that needs the high-level result fast

Requirements:

- keep it within one page when possible
- state target repo and selected reproduction goal
- state overall outcome clearly
- list the main documented command that was attempted or verified
- list the biggest blocker if not successful
- when patches were applied, surface patch state briefly:
  - `patches_applied`
  - patch branch
  - README fidelity impact
  - highest patch risk

## `COMMANDS.md`

Requirements:

- commands must be copyable
- separate setup, assets, run, and verification steps
- label each command as documented, adapted, or inferred
- avoid dumping noise from the shell history

## `LOG.md`

Requirements:

- concise chronological record
- include assumptions, evidence, failures, retries, and decisions
- distinguish between README-backed steps and inferred steps

## `status.json`

Requirements:

- keys remain in English
- enums remain stable
- values can summarize both success and partial verification
- preserve observability for assumptions, deviations, evidence level, and human review points

Suggested top-level keys:

- `schema_version`
- `generated_at`
- `user_language`
- `target_repo`
- `readme_first`
- `selected_goal`
- `goal_priority`
- `status`
- `documented_command_status`
- `documented_command`
- `documented_command_kind`
- `documented_command_source`
- `documented_command_section`
- `patches_applied`
- `patch_branch`
- `readme_fidelity`
- `highest_patch_risk`
- `evidence_level`
- `assumptions`
- `unverified_inferences`
- `protocol_deviations`
- `human_decisions_required`
- `next_safe_action`
- `artifact_provenance`
- `verified_commit_count`
- `outputs`
- `notes`

Recommended status enums:

- `success`
- `partial`
- `blocked`
- `not_run`

Recommended evidence level enums:

- `direct`
- `mixed`
- `inferred`

Field intent:

- `assumptions`
  - important assumptions that still shape execution or interpretation
- `unverified_inferences`
  - bounded inferences that were useful but not directly verified
- `protocol_deviations`
  - meaningful differences from README, paper, or documented setup
- `human_decisions_required`
  - decisions that should not be taken implicitly by the agent
- `next_safe_action`
  - the lowest-risk next step a researcher can review or run
- `artifact_provenance`
  - where key inputs or outputs came from, such as README, repo path, paper, dataset root, checkpoint, or generated logs

## `PATCHES.md`

Only create this file when repository files were modified.

Requirements:

- record patch branch name
- record highest patch risk
- record verified commits in order
- explain what changed and why for each verified commit
- explain how each change was verified
- state whether README fidelity was preserved, clarified, or diverged
- record changed files for each verified commit
- keep human-readable prose in the user's language when practical, but preserve commit hashes, branch names, and command strings verbatim
