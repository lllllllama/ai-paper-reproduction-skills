# Architecture

This repository is organized as one main orchestration skill plus four narrow sub-skills.

## Main idea

The main skill controls policy and output shape.

Sub-skills handle focused tasks:

- repo intake and planning
- environment and asset preparation
- minimal execution and auditing
- optional paper context resolution

## Why this split

- It keeps the main skill readable.
- It makes boundaries easy to extend.
- It avoids turning every reproduction task into a monolithic prompt.
- It supports selective reuse of sub-skills in custom workflows.

## Data flow

1. `repo-intake-and-plan`
   - scans repo structure
   - extracts candidate commands
   - proposes the smallest credible target
2. `env-and-assets-bootstrap`
   - maps dependencies, paths, and assets
   - writes conservative setup notes
3. `minimal-run-and-audit`
   - executes smoke or main documented commands
   - emits standardized outputs
4. `paper-context-resolver` optional
   - fills reproduction-critical gaps only

## Output strategy

Human-readable outputs are concise and easy to scan.

Machine-readable output remains stable:

- fixed filenames
- English keys
- predictable status enums

## Non-goals

- full lab automation
- benchmark orchestration across many repos
- generic paper summarization
- unconstrained code patching
