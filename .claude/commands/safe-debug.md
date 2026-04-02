---
description: Diagnose a research repository failure conservatively before patching.
argument-hint: [traceback, failing command, or debug focus]
---

Read and follow @skills/safe-debug/SKILL.md.

Use the current conversation context plus `$ARGUMENTS` as the failure report. If there is still no actionable traceback, command output, or failure description, ask for the missing failure context instead of guessing.

Stay in the safe-debug lane:

- diagnose before patching
- prefer the smallest safe fix
- do not treat this as exploratory work
- preserve scientific meaning and trusted-lane semantics

Additional user context: $ARGUMENTS
