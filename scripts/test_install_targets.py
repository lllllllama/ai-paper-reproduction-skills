#!/usr/bin/env python3
"""Regression checks for Codex and Claude Code installer target resolution."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from install_skills import default_target, install_skills


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    temp_root = Path(tempfile.mkdtemp(prefix="codex-install-targets-", dir=repo_root))
    try:
        codex_home = temp_root / "codex-home"
        claude_home = temp_root / "claude-home"
        fake_home = temp_root / "fake-home"

        codex_target = default_target("codex", env={"CODEX_HOME": str(codex_home)}, home=fake_home)
        claude_target = default_target("claude", env={"CLAUDE_HOME": str(claude_home)}, home=fake_home)
        fallback_claude_target = default_target("claude", env={}, home=fake_home)

        if codex_target != (codex_home / "skills").resolve():
            raise AssertionError("codex target resolution ignored CODEX_HOME")
        if claude_target != (claude_home / "skills").resolve():
            raise AssertionError("claude target resolution ignored CLAUDE_HOME")
        if fallback_claude_target != (fake_home / ".claude" / "skills").resolve():
            raise AssertionError("claude fallback target did not resolve to ~/.claude/skills")

        installed = install_skills(repo_root, temp_root / "installed-skills", mode="copy", force=False)
        if len(installed) != len(list((repo_root / "skills").glob("*/SKILL.md"))):
            raise AssertionError("installer did not copy the full skill set")
        if not all((path / "SKILL.md").exists() for path in installed):
            raise AssertionError("installer lost SKILL.md during copy")

        print("ok: True")
        print("checks: 5")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())
