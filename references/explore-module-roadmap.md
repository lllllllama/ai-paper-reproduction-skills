# Explore Module Roadmap

## Status

Planning document only. This roadmap describes how to evolve the current explore lane from a safe planning layer into a stronger execution-capable research workflow.

## Current Assessment

The current explore module already has a sound shape:

- `research-explore` is the only end-to-end public orchestrator in the explore lane.
- `explore-code` and `explore-run` are narrow public leaf skills.
- all explore outputs converge into `explore_outputs/`
- `current_research` is the explicit anchor for exploratory work

The current weakness is not routing. The weakness is execution depth.

Today the explore lane is stronger at:

- boundary control
- planning and summarization
- recording candidate-only outputs

It is weaker at:

- actually enforcing isolated workspaces
- actually dispatching code and run work as a coordinated workflow
- pruning exploratory run matrices before they get large
- promoting good exploratory results into a human-review checkpoint

## Design Goal

Make the explore lane good at real research iteration without making it unsafe.

That means:

- keep explicit exploratory authorization
- keep candidate-only outputs
- keep trusted and explore lanes separate
- add stronger orchestration and execution behavior
- avoid turning explore into an unconstrained autonomous researcher

## Roadmap Summary

### P0: Make the current orchestrator real

Goal:

- upgrade `research-explore` from a planning-heavy orchestrator into a real coordinator with stronger local execution guarantees

Deliverables:

- create or validate an isolated branch or worktree instead of only naming one
- make `research-explore` explicitly invoke repository-local explore helpers rather than only recording a planned chain
- preserve one canonical explore context object across code, run, and output phases
- keep `current_research`, `experiment_branch`, and `explicit_explore_authorization` mandatory in the shared status payload

Implementation targets:

- `skills/research-explore/scripts/orchestrate_explore.py`
- `shared/scripts/write_explore_bundle.py`
- `references/branch-and-commit-policy.md`
- `scripts/test_research_explore_dry_run.py`

Acceptance criteria:

- a dry run proves the orchestrator resolved one isolated branch or worktree
- the orchestrator emits a trace of which local helper stages were actually invoked
- the output bundle records one stable context object across all emitted files
- failure to provide a durable `current_research` is rejected early

Non-goals for P0:

- full automatic experiment execution
- large-scale search strategies
- trusted-lane promotion logic

### P1: Strengthen the leaf skills

Goal:

- make `explore-code` and `explore-run` materially useful on their own, not just cleanly described

Deliverables:

- add a real planning or execution helper for `explore-code`
- add budget-aware pruning to `explore-run`
- record stronger run metadata for candidate comparison
- make code-only and run-only outputs more mode-specific while preserving the shared schema

Implementation targets:

- `skills/explore-code/scripts/`
- `skills/explore-run/scripts/plan_variants.py`
- `skills/explore-code/references/explore-policy.md`
- `skills/explore-run/references/execution-policy.md`
- `scripts/test_explore_variant_matrix.py`
- `scripts/test_explore_output_rendering.py`

Acceptance criteria:

- `explore-code` can produce a concrete edit plan or patch summary before broader orchestration
- `explore-run` supports run-budget controls such as max variants or max short-cycle candidates
- `explore-run` ranks candidates using explicit metric fields when present
- both leaf skills emit mode-specific notes without drifting from the shared `explore_outputs/` schema

Non-goals for P1:

- automatic idea generation without repository grounding
- remote scheduler integration

### P2: Add human review checkpoints

Goal:

- make exploratory outcomes easier to continue, compare, and selectively promote without collapsing them into trusted claims

Deliverables:

- add explicit review states such as `planned`, `running`, `ranked`, `needs-review`, `candidate-selected`
- introduce a human-review summary for whether a candidate is worth further trusted verification
- separate "interesting result" from "trusted result" in status and docs
- define a narrow bridge from explore outputs into later trusted follow-up work

Implementation targets:

- `shared/scripts/write_explore_bundle.py`
- `references/output-contract.md`
- `references/routing-policy.md`
- `references/trigger-boundary-policy.md`
- `scripts/test_explore_output_rendering.py`

Acceptance criteria:

- outputs clearly distinguish exploratory ranking from trusted confirmation
- a human can tell from `status.json` whether the next step is more exploration or a trusted follow-up
- no explore output implies trusted success without an explicit later trusted-lane action

Non-goals for P2:

- automatic promotion into trusted reproduction
- merging explore and trusted schemas

## Recommended Sequence

1. Finish P0 before widening P1.
2. Finish run-budget controls before adding more exploratory axes.
3. Add human-review checkpoints only after the orchestrator and leaf skills have stable context fields.

Reasoning:

- without P0, the module still behaves mostly like a planner
- without P1 pruning, stronger orchestration just makes it easier to generate too many weak candidate runs
- without stable context, review-state fields become noisy and fragile

## Highest-Value Near-Term Changes

If only three things get built next, they should be:

1. actual isolated branch or worktree handling in `research-explore`
2. budget-aware pruning in `explore-run`
3. a concrete planner helper for `explore-code`

These three changes improve the module more than cosmetic routing or naming tweaks.

## Risks To Avoid

- turning `research-explore` into a vague idea generator
- letting `explore-run` expand combinatorially without budget controls
- letting exploratory outputs imply trusted baseline improvement
- making the leaf skills depend on tools or skills that are not bundled in this repository
- adding execution depth without keeping audit trails in `explore_outputs/`

## Open Questions

- Should `research-explore` require a metric name before candidate ranking starts, or allow pure structural exploration first
- Should `explore-code` remain public after it gains a stronger planner, or should it eventually narrow toward helper status
- Should `explore-run` support a repository-local notion of experiment budget in the shared explore schema
- Should there be a later `trusted-followup` helper that consumes selected explore candidates without changing lane semantics

## Exit Condition

This roadmap is complete when the explore lane can do all of the following reliably:

- start from a durable `current_research`
- create isolated exploratory context
- coordinate code and run exploration in one flow
- keep candidate ranking bounded and reviewable
- hand off only by explicit human decision into a later trusted step
