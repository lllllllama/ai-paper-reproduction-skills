#!/usr/bin/env python3
"""Regression checks for Claude Code project command wrappers."""

from __future__ import annotations

from pathlib import Path


EXPECTED_COMMANDS = {
    "ai-paper-reproduction": "skills/ai-paper-reproduction/SKILL.md",
    "research-explore": "skills/research-explore/SKILL.md",
    "analyze-project": "skills/analyze-project/SKILL.md",
    "safe-debug": "skills/safe-debug/SKILL.md",
}


def parse_front_matter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"{path} is missing YAML front matter")

    try:
        _, front_matter, _ = text.split("---", 2)
    except ValueError as exc:
        raise AssertionError(f"{path} has malformed YAML front matter") from exc

    data: dict[str, str] = {}
    for raw_line in front_matter.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    commands_root = repo_root / ".claude" / "commands"

    for command_name, skill_path in EXPECTED_COMMANDS.items():
        command_path = commands_root / f"{command_name}.md"
        if not command_path.exists():
            raise AssertionError(f"Missing Claude project command wrapper: {command_path}")

        front_matter = parse_front_matter(command_path)
        if "description" not in front_matter or not front_matter["description"]:
            raise AssertionError(f"{command_path} is missing a description")
        if "argument-hint" not in front_matter or not front_matter["argument-hint"]:
            raise AssertionError(f"{command_path} is missing an argument-hint")

        text = command_path.read_text(encoding="utf-8")
        if f"@{skill_path}" not in text:
            raise AssertionError(f"{command_path} does not reference @{skill_path}")
        if "$ARGUMENTS" not in text:
            raise AssertionError(f"{command_path} does not pass through $ARGUMENTS")

    print("ok: True")
    print(f"checks: {len(EXPECTED_COMMANDS) * 4}")
    print("failures: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
