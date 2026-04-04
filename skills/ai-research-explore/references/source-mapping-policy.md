# Source Mapping Policy

Source mapping in `ai-research-explore` is for bounded, auditable adaptation only.

## Required Outputs

- source repo or source reference id
- source file and source symbol when known
- target file and target symbol
- supporting files
- interface diff summary
- minimal reversible patch plan

## Patch Classes

- `config-only`
- `import-glue`
- `module-transplant-shim`

These classes are preferred in that order.

## Forbidden Defaults

- broad rewrites
- train-loop redesign
- metric or leaderboard mutation without explicit campaign permission
- unscoped multi-module behavior changes

