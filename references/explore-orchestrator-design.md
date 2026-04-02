# Explore Orchestrator Design

## Status

Proposed design only. This document does not change the current public skill set by itself.

## Problem

The repository already has a clear trusted-lane main orchestrator:

- `ai-paper-reproduction` for end-to-end README-first trustworthy reproduction

It also has two explore-lane public skills:

- `explore-code` for isolated exploratory code changes
- `explore-run` for isolated exploratory runs

This works for narrow explicit requests, but it leaves a gap for a common research workflow:

- `current_research` has already been produced, improved, or selected
- the researcher now wants end-to-end exploratory iteration on top of that context
- the task may require both code adaptation and ranked candidate runs
- the user wants one explicit explore entrypoint rather than deciding between code-only and run-only skills first

## Decision Summary

Add one new public explore-lane orchestrator skill for explicit exploratory iteration on top of `current_research`.

Recommended name:

- `research-explore`

Why this name:

- it makes the research context explicit
- it still fits explicit exploratory intent
- it stays broad enough for post-reproduction or post-improvement iteration
- it does not imply trusted reproduction or paper-faithful claims

## Scope

`research-explore` should be the end-to-end entrypoint when the researcher wants AI to explore on top of `current_research`.

`current_research` may be:

- a faithful paper reproduction
- a previously improved internal model or branch
- a branch, commit, checkpoint, or run record that the researcher names as `current_research`

The orchestrator should treat `current_research` as the comparison anchor for exploration, not as a new trusted claim.

## Primary Use Cases

Use `research-explore` when the request looks like:

- "On top of this reproduced model, try several adapter variants on an isolated branch."
- "Use this improved model as `current_research` and explore a few low-cost candidate ideas."
- "Plan a short-cycle sweep against the current checkpoint and rank candidates."
- "Explore code and run changes together, but keep them isolated from the trusted track."

## Non-Goals

`research-explore` should not:

- replace `ai-paper-reproduction`
- silently convert trusted reproduction into exploration
- act as a generic idea generator without a clear `current_research`
- become a default route for ambiguous "improve this" prompts
- require any skill outside this repository to succeed

## Routing Position

The repository should then have two orchestrators for two different end-to-end task families:

- `ai-paper-reproduction`
  - trusted-lane orchestrator for README-first reproduction
- `research-explore`
  - explore-lane orchestrator for explicit exploration on top of the current experimental foundation

This does not violate the "one main orchestrator" rule.

The rule should be interpreted as:

- one public orchestrator per end-to-end task family
- not one orchestrator for the entire repository regardless of workflow

## Trigger Boundary

`research-explore` should trigger only when both conditions hold:

1. the user explicitly authorizes exploration
2. the request implies multi-step exploratory iteration rather than a narrow code-only or run-only task

Expected positive trigger signals:

- explore
- variant
- candidate
- isolated branch
- worktree
- not trusted baseline
- short-cycle
- small-subset
- sweep
- rank top runs
- on top of this model
- use this checkpoint as `current_research`
- branch off from this run

Expected exclusion signals:

- README-first reproduction
- documented command verification
- paper summary
- generic environment setup
- passive repo familiarization
- narrow code-only exploration
- narrow run-only exploration

## Relationship To Existing Skills

`research-explore` should orchestrate, not replace, the current explore-lane leaf skills.

Recommended relationship:

- keep `explore-code` public for narrow explicit code-adaptation requests
- keep `explore-run` public for narrow explicit run-planning and run-ranking requests
- add `research-explore` as the only explore-lane end-to-end orchestrator

This mirrors the trusted lane structure:

- orchestrator for end-to-end work
- narrower public skills for focused requests

### Why not demote `explore-code` and `explore-run` to helper immediately

That would reduce surface area, but it would also remove useful narrow entrypoints that already have clear intent:

- "adapt this backbone on an isolated branch"
- "run a short-cycle sweep and rank candidates"

Those are legitimate direct asks. Keep them public unless real routing data shows they create excessive overlap.

## Call Graph

`research-explore` should be allowed to call only repository-local skills.

Recommended `can_call` list:

- `analyze-project`
- `env-and-assets-bootstrap`
- `explore-code`
- `explore-run`
- `minimal-run-and-audit`
- `run-train`

Optional helper use:

- `repo-intake-and-plan` only when the repo or command inventory is still unclear

Avoid by default:

- `paper-context-resolver`

Rationale:

- exploration on top of `current_research` usually depends more on code structure and run budget than on paper-gap resolution

## Dependency Policy

`research-explore` must not hard-depend on skills that are not bundled in this repository.

Rules:

- repository-local skills may be required
- external environment skills may be used only as optional accelerators
- if an external skill is absent, the orchestrator must still complete via bundled skills and scripts

This keeps installation simple and avoids "works only if the user happened to install another unrelated skill pack".

## Workflow

Recommended high-level workflow:

1. Confirm `current_research`:
   - branch
   - commit
   - checkpoint
   - run record
   - already-improved local model
2. Confirm that the user is authorizing explore-lane work.
3. Confirm the exploration budget:
   - code change budget
   - run budget
   - evaluation metric
   - stop condition
4. Use `analyze-project` only if insertion points or config relationships are still unclear.
5. Use `env-and-assets-bootstrap` only if the current experimental foundation environment or assets are still ambiguous.
6. If exploratory code changes are required, call `explore-code`.
7. If ranked candidate runs are required, call `explore-run`.
8. Let `explore-code` or `explore-run` hand execution to `minimal-run-and-audit` or `run-train` when needed.
9. Write a disposable but reviewable `explore_outputs/` summary anchored to `current_research`.
10. Never claim trusted reproduction success from exploratory gains.

## Output Contract

To minimize churn, `research-explore` should initially reuse the established explore output shape:

```text
explore_outputs/
  CHANGESET.md
  TOP_RUNS.md
  status.json
```

Required semantics:

- record `current_research`, such as a branch, commit, checkpoint, run, or improved local model state
- record the experiment branch or worktree
- record candidate hypotheses
- record which variants were attempted
- rank top candidates
- state the next exploration-safe action
- clearly mark all results as exploratory candidates only

## `current_research` Semantics

`current_research` does not need to be the original paper checkpoint.

It may be:

- `main@<commit>`
- `improved-model@<branch>`
- `checkpoints/best.pt`
- a run ID or output bundle the researcher names explicitly
- a local model state the researcher identifies as `current_research`

The orchestrator should require `current_research` to be named in some durable form before broader exploration starts.

If the user gives only vague wording such as "the current model", the orchestrator should first ask or infer a precise branch, commit, checkpoint, or run reference from local evidence before branching into exploration.

## Interaction With Trusted Lane

The handoff boundary should be strict:

- `ai-paper-reproduction` must never auto-route into `research-explore`
- `research-explore` must never present outcomes as trusted reproduction success
- trusted outputs stay in `repro_outputs/` and `train_outputs/`
- exploratory outcomes stay in `explore_outputs/`

The researcher may manually move from trusted to explore, but that handoff must be explicit in the prompt or recorded decision.

## Prompt Examples

Prompts that should trigger `research-explore`:

```text
Use research-explore on top of current_research baseline-clean@branch. Work on an isolated branch, try three low-risk adapter variants, run short-cycle checks, and rank the candidates in explore_outputs/.
```

```text
This model is already reproduced and lightly improved. Use it as current_research, explore a few candidate heads and training variants on top of it, keep all work exploratory only, and do not present the results as the trusted baseline.
```

Prompts that should not trigger `research-explore`:

```text
Reproduce this paper repository from the README and verify the documented evaluation command.
```

```text
On an isolated branch, transplant this module and summarize the code changes only.
```

```text
Run a short-cycle sweep on this experiment branch and rank the best runs.
```

The second example belongs to `explore-code`.

The third example belongs to `explore-run`.

## Registry Shape

Recommended future registry entry:

```json
{
  "name": "research-explore",
  "tier": "public",
  "lane": "explore",
  "compat": {
    "preserve_name": true,
    "aliases": []
  },
  "can_call": [
    "analyze-project",
    "env-and-assets-bootstrap",
    "explore-code",
    "explore-run",
    "minimal-run-and-audit",
    "run-train"
  ],
  "required_files": [
    "SKILL.md",
    "references/explore-policy.md",
    "scripts/orchestrate_explore.py",
    "agents/openai.yaml"
  ],
  "output_mode": {
    "kind": "explore",
    "primary_dir": "explore_outputs",
    "artifacts": [
      "CHANGESET.md",
      "TOP_RUNS.md",
      "status.json"
    ]
  }
}
```

## Test Plan

Before implementation is trusted, add:

1. positive trigger cases for explicit exploration on top of `current_research`
2. boundary cases against `ai-paper-reproduction`
3. boundary cases against `explore-code`
4. boundary cases against `explore-run`
5. output rendering tests for `current_research` and experiment branch recording
6. orchestration dry-run tests for mixed code-plus-run exploration
7. negative tests proving ambiguous prompts still default to the trusted lane

## Migration Plan

Recommended order:

1. land this design
2. implement `skills/research-explore/`
3. add trigger and output tests
4. update README and routing docs
5. observe whether `explore-code` and `explore-run` still justify staying public

Do not demote existing public explore skills until real usage shows that the new orchestrator makes them redundant.

## Open Questions

- Should `research-explore` require an explicit metric name up front, or allow code-only exploration first
- Should `repo-intake-and-plan` be callable in explore-lane orchestration when `current_research` metadata is incomplete
- Should `explore_outputs/status.json` gain a first-class `current_research` field before implementation starts
