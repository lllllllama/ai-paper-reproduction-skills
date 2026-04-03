# Research Explore Policy

## Purpose

Use this skill only when exploratory work has been explicitly authorized on top of `current_research`.

## Requirements

- keep work on an isolated branch or worktree
- record `current_research` in a durable form
- treat all outputs as candidate-only exploratory records
- coordinate code and run exploration conservatively instead of freeform rewriting
- keep the trusted lane and exploratory lane clearly separated
- keep improvement mining bounded to the frozen task family, dataset, benchmark, evaluation source, and provided SOTA references
- require source-backed idea cards before transplant-style implementation planning
- keep patch plans minimal, reversible, and auditable
- keep research lookup free-first and provider-optional; missing external keys must not block the flow
- treat `seed_only` lookup records as weak evidence only
- distinguish `external_provider`, `parsed_locator`, `repo_local_extracted`, and `seed_only` evidence in downstream ranking and support summaries

## Avoid

- implicit experimentation
- claiming exploratory gains as trusted reproduction success
- requiring non-bundled skills to complete the workflow
- using this skill for narrow code-only or run-only asks
- open-ended scientific brainstorming without a frozen campaign anchor
- broad multi-module rewrites or metric-surface edits by default
- presenting cache-first locator parsing as complete current-literature retrieval
