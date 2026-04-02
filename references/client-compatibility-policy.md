# Client Compatibility Policy

This repository treats `SKILL.md` as the canonical portable skill format.

## Canonical skill contract

- every skill must have a valid `SKILL.md`
- repository-local scripts and references must be addressable from that skill directory
- core skill behavior must not depend on client-specific metadata files

## Installation targets

Prefer the neutral Agent Skills layout when you want one install target that works across compatible clients:

- `~/.agents/skills/`
- `./.agents/skills/`

Client-specific installs are still supported:

- Codex: `~/.codex/skills/`
- Claude Code: `~/.claude/skills/`

## Metadata policy

`agents/openai.yaml` is optional UI metadata for clients that use it.

Rules:

- do not treat `agents/openai.yaml` as the canonical skill definition
- do not make cross-client behavior depend on `agents/openai.yaml`
- validate `agents/openai.yaml` only when it exists

## Documentation policy

- document neutral install paths first when describing cross-client usage
- keep client-specific examples when they help users adopt the repository
- do not describe Codex-only metadata as if Claude Code requires it
