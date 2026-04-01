# Analysis Policy

## Default stance

Prefer structural understanding over action.

## Required behavior

- identify likely training, inference, and evaluation entrypoints
- summarize config and script layout
- highlight insertion points conservatively
- flag suspicious implementation patterns as unverified heuristics
- keep recommendations low-ego and review-friendly

## Forbidden behavior

- patching repository code
- claiming a suspicious pattern is a confirmed bug without evidence
- running heavy training or evaluation jobs by default
