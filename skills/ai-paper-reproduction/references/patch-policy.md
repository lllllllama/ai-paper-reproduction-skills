# Patch Policy

## Default stance

Avoid patching repository code unless reproduction is blocked and the change is both conservative and auditable.

## Allowed-first changes

Prefer these classes first:

- environment variables
- filesystem path fixes
- dependency pin adjustments
- `requirements.txt` or `environment.yml` corrections
- command-line argument fixes that preserve documented intent

## Allowed-with-caution changes

- small compatibility fixes for modern Python or library versions
- explicit path joins or file existence guards
- OS portability fixes when the documented command remains semantically the same

These still need justification and verification.

## Default disallowed changes

- architecture changes
- dataset label changes
- loss or metric definition changes
- training loop rewrites
- inference output logic rewrites
- silent behavior changes that make the command "pass" but alter experiment meaning

## Branching and commits

Before the first repo file edit, create:

```text
repro/YYYY-MM-DD-short-task
```

Commit only after a verified group of changes.

Preferred commit message:

```text
repro: <scope> for documented <command>
```

Keep verified patch commits sparse:

- ideal: `0-2`
- upper practical bound for this workflow: about `3`

## Reporting

Every patch must be reflected in `PATCHES.md` with:

- branch
- highest risk
- commit hash
- changed files
- rationale
- verification
- README fidelity impact

If no repository files were modified:

- do not create `PATCHES.md`
- keep `patches_applied` false in `status.json`
- keep the explanation in `SUMMARY.md` or `LOG.md` focused on the run and blocker, not on hypothetical patches
