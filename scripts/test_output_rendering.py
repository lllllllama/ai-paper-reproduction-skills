#!/usr/bin/env python3
"""Regression checks for rendered output files."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict


def write_context(path: Path) -> Dict[str, object]:
    context = {
        "schema_version": "1.0",
        "generated_at": "2026-03-30T00:00:00Z",
        "user_language": "zh-CN",
        "target_repo": "D:/demo/repo",
        "readme_first": True,
        "selected_goal": "inference",
        "goal_priority": "inference",
        "status": "partial",
        "documented_command_status": "partial",
        "documented_command": "python demo.py --prompt test",
        "documented_command_kind": "run",
        "documented_command_source": "code_block",
        "documented_command_section": "Usage",
        "result_summary": "已根据 README 证据选择目标 `inference`。",
        "main_blocker": "选定的已文档化命令以退出码 1 结束。",
        "next_action": "先准备环境与资源，再重试该已文档化命令。",
        "setup_commands": [{"label": "adapted", "command": "conda env create -f environment.yml"}],
        "asset_commands": [{"label": "inferred", "command": "# placeholder asset step"}],
        "run_commands": [{"label": "documented", "command": "python demo.py --prompt test"}],
        "verification_commands": [{"label": "inferred", "command": "# placeholder verification step"}],
        "command_notes": [
            "README 路径：D:/demo/repo/README.md",
            "主运行标签：来自 README 的 documented（code_block），章节 `Usage`",
        ],
        "timeline": ["已扫描仓库结构和关键信息文件。"],
        "assumptions": ["README 仍是主要事实来源。"],
        "evidence": ["检测到的文件：README.md"],
        "blockers": ["选定的已文档化命令以退出码 1 结束。"],
        "notes": [],
        "patches_applied": True,
        "patch_branch": "repro/2026-03-30-demo",
        "readme_fidelity": "clarified",
        "highest_patch_risk": "low",
        "verified_commits": [
            {
                "commit": "abc1234",
                "summary": "adjust path handling for documented eval command",
                "files": ["configs/demo.yaml", "scripts/eval.py"],
                "why": ["README 命令在 Windows 上期望使用仓库相对配置路径。"],
                "verification": ["重新运行 `python demo.py --prompt test`，确认配置已正确加载。"],
                "risk": "low",
                "readme_fidelity_effect": "clarified",
            }
        ],
        "validation_summary": "应用 patch 后重新运行已文档化命令，原始失败点已经越过配置加载阶段。",
        "patch_notes": ["Patch stayed within documented command semantics."],
    }
    path.write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding="utf-8")
    return context


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"Missing `{needle}` in {label}")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    writer = repo_root / "skills" / "minimal-run-and-audit" / "scripts" / "write_outputs.py"

    temp_root = Path(tempfile.mkdtemp(prefix="codex-output-render-", dir=repo_root))
    try:
        context_path = temp_root / "context.json"
        output_dir = temp_root / "repro_outputs"
        write_context(context_path)

        subprocess.run(
            [sys.executable, str(writer), "--context-json", str(context_path), "--output-dir", str(output_dir)],
            check=True,
            capture_output=True,
            text=True,
        )

        commands = (output_dir / "COMMANDS.md").read_text(encoding="utf-8")
        summary = (output_dir / "SUMMARY.md").read_text(encoding="utf-8")
        log = (output_dir / "LOG.md").read_text(encoding="utf-8")
        patches = (output_dir / "PATCHES.md").read_text(encoding="utf-8")
        status = json.loads((output_dir / "status.json").read_text(encoding="utf-8"))

        assert_contains(commands, "# 命令", "COMMANDS.md")
        assert_contains(commands, "# [adapted]", "COMMANDS.md")
        assert_contains(commands, "# [documented]", "COMMANDS.md")
        assert_contains(commands, "# [inferred]", "COMMANDS.md")
        assert_contains(summary, "# 复现摘要", "SUMMARY.md")
        assert_contains(summary, "是否应用 patch", "SUMMARY.md")
        assert_contains(summary, "repro/2026-03-30-demo", "SUMMARY.md")
        assert_contains(log, "# 复现日志", "LOG.md")
        assert_contains(log, "命令来源信息", "LOG.md")
        assert_contains(patches, "# Patch 记录", "PATCHES.md")
        assert_contains(patches, "最高 patch 风险", "PATCHES.md")
        assert_contains(patches, "configs/demo.yaml", "PATCHES.md")
        assert_contains(patches, "README 命令", "PATCHES.md")

        if status["user_language"] != "zh-CN":
            raise AssertionError("status.json lost the expected user_language value")
        if status["status"] != "partial":
            raise AssertionError("status.json lost the expected status value")
        if status["documented_command_source"] != "code_block":
            raise AssertionError("status.json lost the expected documented_command_source value")
        if status["documented_command_section"] != "Usage":
            raise AssertionError("status.json lost the expected documented_command_section value")
        if status["patch_branch"] != "repro/2026-03-30-demo":
            raise AssertionError("status.json lost the expected patch_branch value")
        if status["highest_patch_risk"] != "low":
            raise AssertionError("status.json lost the expected highest_patch_risk value")
        if status["verified_commit_count"] != 1:
            raise AssertionError("status.json lost the expected verified_commit_count value")

        print("ok: True")
        print("checks: 17")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())
