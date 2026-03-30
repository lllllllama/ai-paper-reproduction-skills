# Paper-Assisted Reproduction

## Purpose

Use paper context only to unblock README-first reproduction when the repository leaves a critical gap.

Only invoke this step after README and repo inspection already produced a concrete unanswered question.

## Source order

1. paper link explicitly provided by the README
2. official project page or official paper page
3. arXiv or OpenReview primary paper record
4. Google Scholar only to help locate the primary source

## Allowed question types

- dataset version or split
- preprocessing or postprocessing details
- evaluation protocol details
- checkpoint or model variant mapping
- critical runtime assumptions

## Trigger discipline

Good trigger:

- "README is ambiguous about the evaluation split. Check the linked paper and record the conflict if needed."

Bad trigger:

- "Summarize this paper."
- "Find the paper for this repository title and explain it."
- "Tell me everything the paper changed compared with prior work."

## Default exclusions

- full paper summary
- novelty explanation
- broad related-work discussion
- speculative "best settings" not tied to reproduction

## Conflict rule

If README and paper disagree:

- do not silently replace README
- record the conflict
- explain which source says what
- preserve the README-first policy in the final report
