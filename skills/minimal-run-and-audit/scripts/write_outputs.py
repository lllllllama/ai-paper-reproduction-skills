#!/usr/bin/env python3
"""Write standardized reproduction outputs from a context JSON file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


TRANSLATIONS = {
    "en": {
        "none": "None.",
        "no_command": "# No command recorded.",
        "summary_title": "# Reproduction Summary",
        "commands_title": "# Commands",
        "log_title": "# Reproduction Log",
        "patch_title": "# Patch Record",
        "target_repo": "Target repo",
        "selected_goal": "Selected goal",
        "goal_priority": "Goal priority",
        "overall_status": "Overall status",
        "main_documented_command": "Main documented command",
        "command_source": "Command source",
        "command_section": "Command section",
        "patches_applied": "Patches applied",
        "patch_branch": "Patch branch",
        "readme_fidelity": "README fidelity impact",
        "highest_patch_risk": "Highest patch risk",
        "result": "## Result",
        "main_blocker": "## Main blocker",
        "next_action": "## Next action",
        "setup": "## Setup",
        "assets": "## Assets",
        "main_run": "## Main run",
        "verification": "## Verification",
        "notes": "## Notes",
        "context": "## Context",
        "timeline": "## Timeline",
        "assumptions": "## Assumptions",
        "evidence": "## Evidence",
        "command_provenance": "## Command provenance",
        "failures_or_blockers": "## Failures or blockers",
        "user_language": "User language",
        "source": "Source",
        "section": "Section",
        "kind": "Kind",
        "patch_overview": "## Patch overview",
        "verified_commits": "## Verified commits",
        "validation_summary": "## Validation summary",
        "changed_files": "Changed files",
        "why_changed": "Why it changed",
        "verification_method": "How it was verified",
        "risk_level": "Risk level",
        "readme_fidelity_effect": "README fidelity effect",
        "no_validation_summary": "No validation summary recorded.",
    },
    "zh": {
        "none": "无。",
        "no_command": "# 未记录命令。",
        "summary_title": "# 复现摘要",
        "commands_title": "# 命令",
        "log_title": "# 复现日志",
        "patch_title": "# Patch 记录",
        "target_repo": "目标仓库",
        "selected_goal": "已选目标",
        "goal_priority": "目标优先级",
        "overall_status": "整体状态",
        "main_documented_command": "主要已文档化命令",
        "command_source": "命令来源",
        "command_section": "命令章节",
        "patches_applied": "是否应用 patch",
        "patch_branch": "Patch 分支",
        "readme_fidelity": "README 忠实度影响",
        "highest_patch_risk": "最高 patch 风险",
        "result": "## 结果",
        "main_blocker": "## 主要阻塞",
        "next_action": "## 下一步",
        "setup": "## 环境准备",
        "assets": "## 资源",
        "main_run": "## 主运行命令",
        "verification": "## 验证",
        "notes": "## 说明",
        "context": "## 上下文",
        "timeline": "## 时间线",
        "assumptions": "## 假设",
        "evidence": "## 证据",
        "command_provenance": "## 命令来源信息",
        "failures_or_blockers": "## 失败或阻塞",
        "user_language": "用户语言",
        "source": "来源",
        "section": "章节",
        "kind": "类型",
        "patch_overview": "## Patch 概览",
        "verified_commits": "## 已验证提交",
        "validation_summary": "## 验证摘要",
        "changed_files": "修改文件",
        "why_changed": "修改原因",
        "verification_method": "验证方式",
        "risk_level": "风险级别",
        "readme_fidelity_effect": "对 README 忠实度的影响",
        "no_validation_summary": "未记录验证摘要。",
    },
}


def locale(user_language: str) -> str:
    return "zh" if user_language.lower().startswith("zh") else "en"


def tr(user_language: str, key: str) -> str:
    return TRANSLATIONS[locale(user_language)][key]


def bullets(items: Iterable[str], user_language: str = "en") -> str:
    values = [item for item in items if item]
    if not values:
        return f"- {tr(user_language, 'none')}"
    return "\n".join(f"- {item}" for item in values)


def command_block(items: Iterable[Any], user_language: str) -> str:
    values = [item for item in items if item]
    if not values:
        return tr(user_language, "no_command")

    rendered: List[str] = []
    for item in values:
        if isinstance(item, dict):
            label = item.get("label", "inferred")
            command = item.get("command", "")
            rendered.append(f"# [{label}]")
            rendered.append(str(command))
        else:
            rendered.append(str(item))
    return "\n".join(rendered)


def load_context(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def render_commit(item: Dict[str, Any], user_language: str) -> List[str]:
    commit = item.get("commit", "unknown")
    summary = item.get("summary", "No summary provided.")
    files = item.get("files", [])
    why = item.get("why", [])
    verification = item.get("verification", [])
    risk = item.get("risk", "unknown")
    fidelity = item.get("readme_fidelity_effect")

    lines = [f"### `{commit}` {summary}", ""]
    lines.append(f"- {tr(user_language, 'risk_level')}: `{risk}`")
    lines.append(f"- {tr(user_language, 'changed_files')}:")
    lines.extend(f"  - `{path}`" for path in files) if files else lines.append(f"  - {tr(user_language, 'none')}")
    lines.append(f"- {tr(user_language, 'why_changed')}:")
    lines.extend(f"  - {entry}" for entry in why) if why else lines.append(f"  - {tr(user_language, 'none')}")
    lines.append(f"- {tr(user_language, 'verification_method')}:")
    lines.extend(f"  - {entry}" for entry in verification) if verification else lines.append(f"  - {tr(user_language, 'none')}")
    if fidelity:
        lines.append(f"- {tr(user_language, 'readme_fidelity_effect')}: `{fidelity}`")
    lines.append("")
    return lines


def write_summary(output_dir: Path, context: Dict[str, Any]) -> None:
    user_language = context.get("user_language", "en")
    lines = [
        tr(user_language, "summary_title"),
        "",
        f"- {tr(user_language, 'target_repo')}: `{context['target_repo']}`",
        f"- {tr(user_language, 'selected_goal')}: `{context['selected_goal']}`",
        f"- {tr(user_language, 'goal_priority')}: `{context['goal_priority']}`",
        f"- {tr(user_language, 'overall_status')}: `{context['status']}`",
        f"- README-first: `{context['readme_first']}`",
        f"- {tr(user_language, 'main_documented_command')}: `{context['documented_command']}`",
        f"- {tr(user_language, 'command_source')}: `{context.get('documented_command_source', 'none')}`",
        f"- {tr(user_language, 'command_section')}: `{context.get('documented_command_section') or 'none'}`",
        f"- {tr(user_language, 'patches_applied')}: `{context.get('patches_applied', False)}`",
    ]
    if context.get("patches_applied"):
        lines.extend(
            [
                f"- {tr(user_language, 'patch_branch')}: `{context.get('patch_branch', '')}`",
                f"- {tr(user_language, 'readme_fidelity')}: `{context.get('readme_fidelity', 'preserved')}`",
                f"- {tr(user_language, 'highest_patch_risk')}: `{context.get('highest_patch_risk', 'low')}`",
            ]
        )

    lines.extend(
        [
            "",
            tr(user_language, "result"),
            "",
            context["result_summary"],
            "",
            tr(user_language, "main_blocker"),
            "",
            context["main_blocker"],
            "",
            tr(user_language, "next_action"),
            "",
            context["next_action"],
            "",
        ]
    )
    (output_dir / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


def write_commands(output_dir: Path, context: Dict[str, Any]) -> None:
    user_language = context.get("user_language", "en")
    lines = [
        tr(user_language, "commands_title"),
        "",
        tr(user_language, "setup"),
        "",
        "```bash",
        command_block(context.get("setup_commands", []), user_language),
        "```",
        "",
        tr(user_language, "assets"),
        "",
        "```bash",
        command_block(context.get("asset_commands", []), user_language),
        "```",
        "",
        tr(user_language, "main_run"),
        "",
        "```bash",
        command_block(context.get("run_commands", []), user_language),
        "```",
        "",
        tr(user_language, "verification"),
        "",
        "```bash",
        command_block(context.get("verification_commands", []), user_language),
        "```",
        "",
        tr(user_language, "notes"),
        "",
        bullets(context.get("command_notes", []), user_language),
        "",
    ]
    (output_dir / "COMMANDS.md").write_text("\n".join(lines), encoding="utf-8")


def write_log(output_dir: Path, context: Dict[str, Any]) -> None:
    user_language = context.get("user_language", "en")
    lines = [
        tr(user_language, "log_title"),
        "",
        tr(user_language, "context"),
        "",
        f"- {tr(user_language, 'target_repo')}: `{context['target_repo']}`",
        f"- {tr(user_language, 'selected_goal')}: `{context['selected_goal']}`",
        f"- {tr(user_language, 'user_language')}: `{context['user_language']}`",
        "",
        tr(user_language, "timeline"),
        "",
        bullets(context.get("timeline", []), user_language),
        "",
        tr(user_language, "assumptions"),
        "",
        bullets(context.get("assumptions", []), user_language),
        "",
        tr(user_language, "evidence"),
        "",
        bullets(context.get("evidence", []), user_language),
        "",
        tr(user_language, "command_provenance"),
        "",
        bullets(
            [
                f"{tr(user_language, 'main_documented_command')}: `{context.get('documented_command', 'None extracted')}`",
                f"{tr(user_language, 'source')}: `{context.get('documented_command_source', 'none')}`",
                f"{tr(user_language, 'section')}: `{context.get('documented_command_section') or 'none'}`",
                f"{tr(user_language, 'kind')}: `{context.get('documented_command_kind', 'none')}`",
            ],
            user_language,
        ),
        "",
        tr(user_language, "failures_or_blockers"),
        "",
        bullets(context.get("blockers", []), user_language),
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
        "documented_command": context.get("documented_command", "None extracted"),
        "documented_command_kind": context.get("documented_command_kind", "none"),
        "documented_command_source": context.get("documented_command_source", "none"),
        "documented_command_section": context.get("documented_command_section"),
        "patches_applied": context.get("patches_applied", False),
        "patch_branch": context.get("patch_branch") if context.get("patches_applied") else None,
        "readme_fidelity": context.get("readme_fidelity") if context.get("patches_applied") else None,
        "highest_patch_risk": context.get("highest_patch_risk") if context.get("patches_applied") else None,
        "verified_commit_count": len(context.get("verified_commits", [])),
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

    user_language = context.get("user_language", "en")
    lines = [
        tr(user_language, "patch_title"),
        "",
        tr(user_language, "patch_overview"),
        "",
        f"- {tr(user_language, 'patch_branch')}: `{context.get('patch_branch', '')}`",
        f"- {tr(user_language, 'readme_fidelity')}: `{context.get('readme_fidelity', 'preserved')}`",
        f"- {tr(user_language, 'highest_patch_risk')}: `{context.get('highest_patch_risk', 'low')}`",
        "",
        tr(user_language, "verified_commits"),
        "",
    ]

    commits = context.get("verified_commits", [])
    if not commits:
        lines.append(f"- {tr(user_language, 'none')}")
        lines.append("")
    else:
        for item in commits:
            lines.extend(render_commit(item, user_language))

    lines.extend(
        [
            tr(user_language, "validation_summary"),
            "",
            context.get("validation_summary", tr(user_language, "no_validation_summary")),
            "",
            tr(user_language, "notes"),
            "",
            bullets(context.get("patch_notes", []), user_language),
            "",
        ]
    )
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
