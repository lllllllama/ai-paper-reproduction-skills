# Branch And Commit Policy

This repository separates trusted execution from exploratory work.

## Trusted lane

- Prefer no repository patching.
- Before the first non-trivial patch, create a savepoint branch or commit.
- Keep commits sparse and verification-backed.
- Commit messages should describe the documented command or constrained debug scope.

## Explore lane

- Default to an isolated branch or worktree.
- `research-explore` should create or validate the isolated experiment branch before broader exploratory planning continues.
- Direct commits are allowed inside the isolated experiment branch.
- Exploration commits should be disposable and summary-oriented.
- Never merge exploration results back into the trusted baseline without explicit researcher review.
- `explore-code` and `explore-run` should both record the baseline ref and experiment branch in `explore_outputs/`.

## Savepoint guidance

Create a savepoint before:

- medium-risk or high-risk debug patches
- multi-file refactors
- module transplant work
- speculative structure edits

## Reporting

- Trusted lane should record branch, rationale, risk, and verification.
- Explore lane should record baseline ref, experiment branch, source references, and top runs.
