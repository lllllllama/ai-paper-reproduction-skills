# Language Policy

## Goal

Keep human-readable outputs easy for the current user to consume while keeping machine-readable fields stable.

## Rules

- Markdown reports may follow the user's language.
- When language is unknown, default to concise English.
- Do not translate:
  - CLI commands
  - file paths
  - package names
  - config keys
  - code identifiers
- `status.json` keys and enum values stay in English.
- Output filenames stay in English.

## Mixed-language handling

If the user writes in one language but the repository is in another:

- keep technical identifiers exactly as they appear
- localize only the explanatory prose

## Conflict handling

If strict localization would reduce auditability, prefer auditability and keep the wording simpler rather than more translated.
