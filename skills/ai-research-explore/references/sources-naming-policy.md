# Sources Naming Policy

All internal research lookup results for `ai-research-explore` are saved under `sources/`.

## Naming

- summary/index stay at `sources/`
- canonical source records live under `sources/records/`
- record filename format: `kind__slug__sha12.(json|md)`
- `kind` should be stable across reruns such as `paper`, `repo`, `benchmark`, `module`, `query`
- `slug` should be lowercase and human-readable
- `sha12` should be derived from the normalized lookup payload

## Cache Rules

- check `sources/index.json` before creating a new record
- reuse an existing record if the normalized payload hash matches
- preserve source URLs, titles, and lookup queries for auditability

## Scope

- `sources/` is an exploratory audit trail, not a trusted literature database
- source cache entries must not imply benchmark completeness
- source cache entries must not imply novelty proof

