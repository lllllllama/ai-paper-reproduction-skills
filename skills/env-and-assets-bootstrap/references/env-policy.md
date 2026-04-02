# Environment Policy

## Default preference

Prefer conda or Anaconda-style setup for AI paper repositories because it is common in research code and helps isolate conflicting dependencies.

## Order of trust

1. README environment instructions
2. repository environment files
3. package metadata files
4. conservative inference from imports or script names

## OS guidance

- Linux is the default reference environment.
- Support Windows and macOS where practical.
- If a repository is clearly Linux-only, record that rather than pretending otherwise.
- When virtualenv activation is needed, emit platform-specific commands instead of a fake one-size-fits-all activation step.
- Prefer Python entrypoints over shell-only helpers when the same setup logic should run on Windows, macOS, and Linux.

## Dependency handling

- prefer existing `environment.yml`
- otherwise translate README requirements into a simple conda-plus-pip setup
- avoid aggressive upgrades unless needed for a verified fix
- record version uncertainty explicitly

## Out of scope by default

- container orchestration
- cluster schedulers
- custom CUDA builds unless clearly required
