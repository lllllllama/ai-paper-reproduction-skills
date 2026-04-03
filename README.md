# 🚀 ai-paper-reproduction-skills

<p>
  <a href="./README.md">🇺🇸 English</a> ·
  <a href="./README.zh-CN.md">🇨🇳 简体中文</a>
</p>

<p>
  <img alt="trusted by default" src="https://img.shields.io/badge/lane-trusted%20by%20default-1f6feb?style=flat-square">
  <img alt="explicit exploration" src="https://img.shields.io/badge/explore-explicit%20only-238636?style=flat-square">
  <img alt="clients" src="https://img.shields.io/badge/clients-Agent%20Skills%20%C2%B7%20Codex%20%C2%B7%20Claude%20Code-6f42c1?style=flat-square">
  <img alt="skills" src="https://img.shields.io/badge/skills-11-8b949e?style=flat-square">
</p>

Lane-aware skill repository for deep learning research workflows.

> 🧭 Trusted for reproduction, setup, analysis, training verification, and debugging.  
> 🔬 Explore only when the researcher explicitly authorizes candidate-only work.  
> 🤝 Share the same `SKILL.md` skills across Agent Skills, Codex, and Claude Code.

This repository is built around one default rule: `trusted by default`.

- Ambiguous requests route to the trusted lane.
- Exploration requires explicit authorization.
- Trusted outputs are auditable and durable.
- Explore outputs are candidate-only and disposable.

The skills use the open `SKILL.md` layout, so the same repository can be installed into neutral Agent Skills directories as well as Codex and Claude Code. For shared local installs, prefer `~/.agents/skills/` or `./.agents/skills/`. Client-specific installs under `~/.codex/skills/` and `~/.claude/skills/` remain supported.

🛠️ `ai-paper-reproduction` · 🔬 `research-explore` · 🧭 `env-and-assets-bootstrap` · 🔍 `analyze-project` · ✅ `minimal-run-and-audit` · 🧪 `run-train` · 🩺 `safe-debug` · 🧬 `explore-code` · 📈 `explore-run`

## ✨ What This Repo Covers

**In scope**

- README-first AI repository reproduction
- Conservative environment, dataset, checkpoint, and cache planning
- Read-only repository and model analysis
- Trusted training startup verification and bounded training monitoring
- Safe debugging for research repositories
- Explicitly authorized exploratory code and run work
- End-to-end exploratory orchestration on top of `current_research`

**Out of scope**

- General paper summarization
- Unbounded autonomous research agents
- Default large-scale code rewriting
- Implicit experimentation on top of a trusted baseline

## 🧭 Choose an Entry Point

| If you want to... | Use |
|---|---|
| Reproduce a repository end-to-end from the README | `ai-paper-reproduction` |
| Run a third-scenario campaign on top of `current_research` with frozen task, eval, and SOTA inputs | `research-explore` |
| Analyze the repository without editing or running heavy jobs | `analyze-project` |
| Prepare environment, dataset, checkpoint, and cache assumptions | `env-and-assets-bootstrap` |
| Run a documented inference or evaluation command conservatively | `minimal-run-and-audit` |
| Start or resume documented training conservatively | `run-train` |
| Diagnose a traceback or failed training/inference run safely | `safe-debug` |
| Make isolated exploratory code changes only | `explore-code` |
| Run isolated exploratory trials only | `explore-run` |

Bundled helper skills:

- `repo-intake-and-plan`
- `paper-context-resolver`

## 🔀 Lanes

### 🛡️ Trusted lane

Use the trusted lane for reproduction, setup, analysis, bounded execution, training verification, and debugging.

- Primary end-to-end orchestrator: `ai-paper-reproduction`
- Output directories: `repro_outputs/`, `train_outputs/`, `analysis_outputs/`, `debug_outputs/`
- Default stance: preserve scientific meaning, minimize semantic changes, surface assumptions and blockers

### 🔬 Explore lane

Use the explore lane only when the researcher explicitly authorizes candidate-only exploratory work.

- Primary end-to-end orchestrator: `research-explore`
- Narrow leaf skills: `explore-code`, `explore-run`
- Output directory: `explore_outputs/`
- Key anchor: `current_research`

`current_research` should be a durable reference such as a branch, commit, checkpoint, run record, or already-trained local model state. It does not imply a trusted baseline; it is the context the exploration branches from.

### 🧰 Helper lane

Helpers are narrow and should usually be orchestrator-invoked rather than used as the first entry point.

## 🤝 Client Compatibility

`SKILL.md` is the canonical cross-client contract in this repository.

- Required for portability: `SKILL.md`, repository-local `scripts/`, and `references/`
- Optional Codex UI metadata: `agents/openai.yaml`
- Optional Claude Code project entrypoints: `.claude/commands/*.md`
- Not allowed: making skill behavior depend on a client-specific metadata file

See [references/client-compatibility-policy.md](references/client-compatibility-policy.md).

```mermaid
flowchart TD
    A[User request] --> B{Explicit exploration?}
    B -- No --> C[Trusted lane]
    B -- Yes --> D[Explore lane]

    C --> C1[ai-paper-reproduction]
    C --> C2[analyze-project]
    C --> C3[env-and-assets-bootstrap]
    C --> C4[minimal-run-and-audit]
    C --> C5[run-train]
    C --> C6[safe-debug]

    D --> D1[research-explore]
    D --> D2[explore-code]
    D --> D3[explore-run]

    C1 -. helper .-> H1[repo-intake-and-plan]
    C1 -. helper .-> H2[paper-context-resolver]
```

## 📦 Install

Install from a local clone into a neutral Agent Skills directory:

```bash
python scripts/install_skills.py --client agents --target ~/.agents/skills --force
```

Install into a project-scoped neutral Agent Skills directory:

```bash
python scripts/install_skills.py --client agents --target ./.agents/skills --force
```

Install with the default neutral target:

```bash
python scripts/install_skills.py --force
```

Install the full repository skill set in Codex:

```bash
npx skills add lllllllama/ai-paper-reproduction-skills --all
```

Install only the trusted reproduction orchestrator in Codex:

```bash
npx skills add lllllllama/ai-paper-reproduction-skills --skill ai-paper-reproduction
```

Install from a local clone into Codex:

```bash
python scripts/install_skills.py --client codex --target ~/.codex/skills --force
```

Install from a local clone into Claude Code:

```bash
python scripts/install_skills.py --client claude --target ~/.claude/skills --force
```

Install into a project-scoped Claude Code skills directory:

```bash
python scripts/install_skills.py --client claude --target ./.claude/skills --force
```

Claude Code can auto-invoke these skills when the descriptions match, or you can call them directly with commands such as `/ai-paper-reproduction`, `/research-explore`, and `/safe-debug`.

This repository also ships project-scoped Claude Code slash commands under `.claude/commands/` for the main entrypoints:

- `/ai-paper-reproduction`
- `/research-explore`
- `/analyze-project`
- `/safe-debug`

## 🧩 Public Skill Matrix

| Lane | Skill | Purpose |
|---|---|---|
| Trusted | `ai-paper-reproduction` | End-to-end README-first reproduction orchestrator |
| Trusted | `env-and-assets-bootstrap` | Conservative environment, dataset, checkpoint, and cache planning |
| Trusted | `minimal-run-and-audit` | Trusted inference, evaluation, smoke, and sanity execution |
| Trusted | `analyze-project` | Read-only project analysis, model mapping, and risk surfacing |
| Trusted | `run-train` | Training startup verification, resume handling, bounded monitoring, and training records |
| Trusted | `safe-debug` | Research-safe debugging: analyze first, patch only after approval |
| Explore | `research-explore` | Third-scenario exploratory orchestration on top of `current_research` with repo understanding, idea gating, and governed experiments |
| Explore | `explore-code` | Exploratory code adaptation, transplant, and stitching on isolated branches |
| Explore | `explore-run` | Small-subset probes, short-cycle trials, and ranked exploratory runs |
| Helper | `repo-intake-and-plan` | Narrow helper for repo scanning and README command extraction |
| Helper | `paper-context-resolver` | Narrow helper for README-paper gap resolution |

## 🔄 Core Flows

### 🛠️ Trusted reproduction flow

`ai-paper-reproduction` follows this high-level sequence:

1. Scan the repository structure and README.
2. Extract documented commands.
3. Choose the smallest trustworthy target in this order:
   - documented inference
   - documented evaluation
   - documented training
4. Generate a conservative environment and asset plan.
5. Execute through `minimal-run-and-audit` or `run-train`.
6. Write `repro_outputs/`.
7. If training was selected, also write `train_outputs/`.

### 🧪 Trusted training semantics

Training is intentionally conservative in the trusted lane.

- If the README exposes a smaller documented inference or evaluation target, the orchestrator prefers that first.
- If training is the current smallest trustworthy target, `run-train` starts with startup verification or a short monitored training check.
- The trusted lane does not silently convert this into an open-ended long run.
- The output should surface the fuller training command, a conservative duration hint, and the next safe action for the researcher.

### 🔬 Exploratory research flow

`research-explore` is now optimized for the third scenario: the researcher has already frozen the task family, dataset, evaluation method, and provided SOTA table, and wants the AI to govern implementation and experiments on top of `current_research`.

1. Confirm `current_research`.
2. Create or reserve an isolated experiment branch or worktree.
3. Produce repository-understanding artifacts in `analysis_outputs/`.
4. Cache research lookup records into `sources/`; current lookup is free-first, cache-first, provider-optional, repo-aware, and provider-limited rather than open-ended search.
5. Run a baseline gate against the provided evaluation command and SOTA table.
6. Build a bounded improvement bank and hypothesis cards.
7. Run an idea gate across the supplied candidate directions.
8. Build source mapping, heuristic interface diff, minimal patch planning, and execution feasibility.
9. Build a single-variable experiment manifest.
10. Run short-cycle candidate execution, and optionally a later full run only if feasibility and checkpoints remain clear.
11. Keep all results candidate-only.
12. Write `explore_outputs/`.

The explore lane must not claim trusted reproduction success, global benchmark completeness, or verified novelty.

### Campaign Inputs

`research-explore` still accepts a plain `variant_spec.json`, but the preferred input for the third scenario is `research_campaign.json` or `research_campaign.yaml`.

The campaign should freeze:

- `task_family`
- `dataset`
- `benchmark`
- `evaluation_source`
- `sota_reference`
- `candidate_ideas`
- `compute_budget`
- `variant_spec`

Optional campaign blocks:

- `research_lookup`
- `idea_policy`
- `source_constraints`
- `feasibility_policy`

See [skills/research-explore/references/research-campaign-spec.md](skills/research-explore/references/research-campaign-spec.md).

### 📈 Exploratory candidate ranking

Before execution, `explore-run` now ranks candidates with three factors instead of cost alone:

- `cost`: cheaper candidates are preferred
- `success_rate`: candidates that are more likely to run cleanly are preferred
- `expected_gain`: candidates that are more likely to produce a measurable improvement are preferred

Default pre-execution weights are:

- `cost = 0.25`
- `success_rate = 0.35`
- `expected_gain = 0.40`

Budget is still enforced through `max_variants` and `max_short_cycle_runs`. After candidates actually run, `research-explore` switches to real execution evidence and ranks results by `status` plus `primary_metric` / `metric_goal` when provided.

For campaign-style idea ranking, `research-explore` now uses hard gates plus weighted scoring. Hard gates screen `single_variable_fit`, `interface_fit`, `patch_surface`, `dependency_drag`, `eval_risk`, and short-run feasibility. Soft scoring then prefers upside, interface fit, rollback ease, innovation story strength, and source support while penalizing implementation drag and broader patch surface.

Minimal variant-spec example:

```json
{
  "current_research": "improved-model@branch",
  "base_command": "python train.py --config configs/demo.yaml",
  "variant_axes": {
    "adapter": ["none", "lora"],
    "lr": ["1e-4", "5e-5"]
  },
  "subset_sizes": [128, 512],
  "short_run_steps": [100, 300],
  "max_variants": 4,
  "max_short_cycle_runs": 2,
  "selection_weights": {
    "cost": 0.25,
    "success_rate": 0.35,
    "expected_gain": 0.40
  },
  "primary_metric": "val_acc",
  "metric_goal": "maximize"
}
```

## 📁 Output Directories

| Directory | Purpose |
|---|---|
| `repro_outputs/` | Trusted reproduction bundle |
| `train_outputs/` | Trusted training execution bundle |
| `analysis_outputs/` | Read-only project analysis, research map, change map, eval contract, improvement bank, idea cards, mapping, and resource plan |
| `debug_outputs/` | Safe debug diagnosis and patch plan |
| `sources/` | Free-first research lookup records with `sources/records/`, stable names, bounded provider resolution, repo-local extraction, and an auditable index |
| `explore_outputs/` | Exploratory changeset, idea gate, experiment plan, experiment manifest, split static/runtime smoke reporting, ledger, and ranked run summary |

## 💬 Example Prompts

**Trusted reproduction**

```text
Use ai-paper-reproduction on this AI repo. Stay README-first, prefer documented inference or evaluation, avoid unnecessary repo changes, and write outputs to repro_outputs/.
```

**Current-research exploration**

```text
Use research-explore on top of current_research improved-model@branch. Work on an isolated branch, coordinate code and run exploration together, try several variants, and rank candidates in explore_outputs/.
```

**Third-scenario campaign exploration**

```text
Use research-explore with research_campaign.json. Treat the provided task family, dataset, evaluation source, and SOTA table as frozen inputs, rank the candidate ideas, keep each candidate single-variable, and write governed outputs to analysis_outputs/ and explore_outputs/.
```

**Read-only analysis**

```text
Use analyze-project on this repo. Read the code, map the model and training entrypoints, and flag suspicious patterns without editing files.
```

**Trusted training**

```text
Use run-train on this repo. Run the selected documented training command conservatively for startup verification and write train_outputs/.
```

**Safe debug**

```text
Use safe-debug on this traceback. Diagnose the failure first, propose the smallest safe fix, and do not patch until I approve.
```

**Exploratory code only**

```text
Use explore-code on an isolated branch. Try a LoRA adaptation for this backbone, keep it exploratory only, and summarize the changes in explore_outputs/.
```

**Exploratory runs only**

```text
Use explore-run on an experiment branch. Do a small-subset short-cycle sweep, rank the top runs, and treat the results as candidates only.
```

## ✅ Local Validation

Run the repository checks:

```bash
python scripts/validate_repo.py
python scripts/test_skill_registry.py
python scripts/test_trigger_boundaries.py
python scripts/test_claude_command_wrappers.py
python scripts/test_readme_selection.py
```

Run output and orchestration regressions:

```bash
python scripts/test_output_rendering.py
python scripts/test_train_output_rendering.py
python scripts/test_analysis_output_rendering.py
python scripts/test_safe_debug_output_rendering.py
python scripts/test_explore_output_rendering.py
python scripts/test_explore_variant_matrix.py
python scripts/test_research_explore_dry_run.py
python scripts/test_research_explore_campaign_flow.py
python scripts/test_research_explore_campaign_abandon.py
python scripts/test_research_explore_campaign_checkpoint.py
python scripts/test_orchestrator_dry_run.py
python scripts/test_training_lane_routing.py
```

Run setup and installer regressions:

```bash
python scripts/test_bootstrap_env.py
python scripts/test_install_targets.py
python scripts/test_setup_planning.py
python scripts/install_skills.py --client agents --target ./tmp/agents-skills --force
python scripts/install_skills.py --client codex --target ./tmp/codex-skills --force
python scripts/install_skills.py --client claude --target ./tmp/claude-skills --force
```

GitHub Actions validates this repository on `ubuntu-latest`, `macos-latest`, and `windows-latest`.

## 📐 Routing Summary

- Ambiguous requests go to the trusted lane.
- Exploration requires explicit authorization.
- Trusted skills must not auto-route into exploration.
- Explore outputs must not claim trusted reproduction success.
- Peer leaf skills should not call each other directly.
- End-to-end orchestration should happen through the public orchestrator for the relevant task family.

## 📚 References

- Skill registry: [references/skill-registry.json](references/skill-registry.json)
- Explore variant spec: [references/explore-variant-spec.md](references/explore-variant-spec.md)
- Explore module roadmap: [references/explore-module-roadmap.md](references/explore-module-roadmap.md)
- Client compatibility policy: [references/client-compatibility-policy.md](references/client-compatibility-policy.md)
- Routing policy: [references/routing-policy.md](references/routing-policy.md)
- Trigger boundary policy: [references/trigger-boundary-policy.md](references/trigger-boundary-policy.md)
- Branch and commit policy: [references/branch-and-commit-policy.md](references/branch-and-commit-policy.md)
- Output contract: [references/output-contract.md](references/output-contract.md)
- Research pitfall checklist: [references/research-pitfall-checklist.md](references/research-pitfall-checklist.md)

## ⚠️ Current Limits

- `run-train` is a bounded training monitor, not a full long-running scheduler.
- Trusted reproduction still avoids silent semantic changes.
- Helper skills remain narrow and are not intended to become public catch-all entry points.
- Exploratory work must stay isolated from trusted baselines.

## 🎯 Scope

This is a lane-aware deep learning research skill repository optimized for safety, observability, and reuse.
