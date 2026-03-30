#!/usr/bin/env python3
"""Regression checks for rendered output files.

This script validates two release-critical properties:

1. human-readable Markdown follows the requested user language when set to Chinese
2. COMMANDS.md includes the documented/adapted/inferred labels required by the output spec
"""

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
        "timeline": ["已扫描仓库结构和关键元数据文件。"],
        "assumptions": ["README 仍是主要事实来源。"],
        "evidence": ["检测到的文件：README.md"],
        "blockers": ["选定的已文档化命令以退出码 1 结束。"],
        "notes": [],
        "patches_applied": False,
        "patch_branch": "",
        "verified_commits": [],
        "validation_summary": "",
        "patch_notes": [],
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
        status = json.loads((output_dir / "status.json").read_text(encoding="utf-8"))

        assert_contains(commands, "# 命令", "COMMANDS.md")
        assert_contains(commands, "# [adapted]", "COMMANDS.md")
        assert_contains(commands, "# [documented]", "COMMANDS.md")
        assert_contains(commands, "# [inferred]", "COMMANDS.md")
        assert_contains(summary, "# 复现摘要", "SUMMARY.md")
        assert_contains(log, "# 复现日志", "LOG.md")

        if status["user_language"] != "zh-CN":
            raise AssertionError("status.json lost the expected user_language value")
        if status["status"] != "partial":
            raise AssertionError("status.json lost the expected status value")

        print("ok: True")
        print("checks: 7")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())
