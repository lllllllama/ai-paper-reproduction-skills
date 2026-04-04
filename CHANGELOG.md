# Changelog

## v1.0.0

Initial public release of `ai-research-workflow-skills`.

### Scope

- README-first reproduction of AI paper repositories
- one main orchestration skill plus four narrow sub-skills
- inference and evaluation first
- training only as startup or partial verification unless explicitly needed
- conservative patching with standardized outputs

### Rename compatibility

- repository brand: ai-research-workflow-skills
- ai-paper-reproduction renamed to ai-research-reproduction
- research-explore renamed to ai-research-explore

### Included skills

- `ai-research-reproduction`
  - main orchestration for README-first target selection, policy control, and output normalization
- `repo-intake-and-plan`
  - scans the repository and extracts documented commands
- `env-and-assets-bootstrap`
  - prepares conservative environment and asset assumptions
- `minimal-run-and-audit`
  - normalizes execution evidence and writes `repro_outputs/`
- `paper-context-resolver`
  - optional paper-assisted gap resolution for reproduction-critical details only

### Output contract

The standardized output directory is:

```text
repro_outputs/
  SUMMARY.md
  COMMANDS.md
  LOG.md
  status.json
  PATCHES.md   # only when repository files changed
```

### Validation

Release validation currently includes:

- repository structure validation
- trigger boundary regression checks
- README command selection regression checks
- rendered output regression checks

### Real-repo trials

The main flow has been trialed against a small set of public AI repositories. See [examples/real_repo_trials.md](examples/real_repo_trials.md).

### Known limits

- environment and asset preparation stays conservative and lightweight
- multilingual human-readable output currently focuses on English and Chinese
- the repository is intentionally not a general paper summary, benchmark design, or experiment orchestration system

