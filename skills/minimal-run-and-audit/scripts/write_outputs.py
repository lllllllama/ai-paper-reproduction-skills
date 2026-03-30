#!/usr/bin/env python3
"""Write standardized reproduction outputs from a context JSON file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def bullets(items: Iterable[str]) -> str:
    values = [item for item in items if item]
    if not values:
        return "- None."
    return "\n".join(f"- {item}" for item in values)


def command_block(items: Iterable[str]) -> str:
    values = [item for item in items if item]
    return "\n".join(values) if values else "# No command recorded."


def load_context(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_summary(output_dir: Path, context: Dict[str, Any]) -> None:
    lines = [
        "# Reproduction Summary",
        "",
        f"- Target repo: `{context['target_repo']}`",
        f"- Selected goal: `{context['selected_goal']}`",
        f"- Goal priority: `{context['goal_priority']}`",
        f"- Overall status: `{context['status']}`",
        f"- README-first: `{context['readme_first']}`",
        f"- Main documented command: `{context['documented_command']}`",
        "",
        "## Result",
        "",
        context["result_summary"],
        "",
        "## Main blocker",
        "",
        context["main_blocker"],
        "",
        "## Next action",
        "",
        context["next_action"],
        "",
    ]
    (output_dir / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


def write_commands(output_dir: Path, context: Dict[str, Any]) -> None:
    lines = [
        "# Commands",
        "",
        "## Setup",
        "",
        "```bash",
        command_block(context.get("setup_commands", [])),
        "```",
        "",
        "## Assets",
        "",
        "```bash",
        command_block(context.get("asset_commands", [])),
        "```",
        "",
        "## Main run",
        "",
        "```bash",
        command_block(context.get("run_commands", [])),
        "```",
        "",
        "## Verification",
        "",
        "```bash",
        command_block(context.get("verification_commands", [])),
        "```",
        "",
        "## Notes",
        "",
        bullets(context.get("command_notes", [])),
        "",
    ]
    (output_dir / "COMMANDS.md").write_text("\n".join(lines), encoding="utf-8")


def write_log(output_dir: Path, context: Dict[str, Any]) -> None:
    lines = [
        "# Reproduction Log",
        "",
        "## Context",
        "",
        f"- Target repo: `{context['target_repo']}`",
        f"- Selected goal: `{context['selected_goal']}`",
        f"- User language: `{context['user_language']}`",
        "",
        "## Timeline",
        "",
        bullets(context.get("timeline", [])),
        "",
        "## Assumptions",
        "",
        bullets(context.get("assumptions", [])),
        "",
        "## Evidence",
        "",
        bullets(context.get("evidence", [])),
        "",
        "## Failures or blockers",
        "",
        bullets(context.get("blockers", [])),
        "",
    ]
    (output_dir / "LOG.md").write_text("\n".join(lines), encoding="utf-8")


def write_status(output_dir: Path, context: Dict[str, Any]) -> None:
    payload = {
        "schema_version": context.get("schema_version", "1.0"),
        "generated_at": context.get("generated_at"),
        "user_language": context.get("user_language", "en"),
        "target_repo": context.get("target_repo"),
        "readme_first": context.get("readme_first", True),
        "selected_goal": context.get("selected_goal", "unknown"),
        "goal_priority": context.get("goal_priority", "other"),
        "status": context.get("status", "not_run"),
        "documented_command_status": context.get("documented_command_status", "not_run"),
        "patches_applied": context.get("patches_applied", False),
        "outputs": {
            "summary": "repro_outputs/SUMMARY.md",
            "commands": "repro_outputs/COMMANDS.md",
            "log": "repro_outputs/LOG.md",
            "status": "repro_outputs/status.json",
            "patches": "repro_outputs/PATCHES.md" if context.get("patches_applied") else None,
        },
        "notes": context.get("notes", []),
    }
    (output_dir / "status.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_patches(output_dir: Path, context: Dict[str, Any]) -> None:
    if not context.get("patches_applied"):
        return

    commit_lines: List[str] = []
    for item in context.get("verified_commits", []):
        commit_lines.append(
            f"- `{item.get('commit', 'unknown')}`: {item.get('summary', 'No summary provided.')}"
        )

    lines = [
        "# Patch Record",
        "",
        f"- Patch branch: `{context.get('patch_branch', '')}`",
        f"- README fidelity impact: `{context.get('readme_fidelity', 'preserved')}`",
        "",
        "## Verified commits",
        "",
        "\n".join(commit_lines) if commit_lines else "- None.",
        "",
        "## Validation summary",
        "",
        context.get("validation_summary", "No validation summary recorded."),
        "",
        "## Notes",
        "",
        bullets(context.get("patch_notes", [])),
        "",
    ]
    (output_dir / "PATCHES.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Write standardized reproduction outputs.")
    parser.add_argument("--context-json", required=True, help="Path to a context JSON file.")
    parser.add_argument(
        "--output-dir",
        default="repro_outputs",
        help="Directory where output files will be written.",
    )
    args = parser.parse_args()

    context = load_context(Path(args.context_json).resolve())
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    write_summary(output_dir, context)
    write_commands(output_dir, context)
    write_log(output_dir, context)
    write_status(output_dir, context)
    write_patches(output_dir, context)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
