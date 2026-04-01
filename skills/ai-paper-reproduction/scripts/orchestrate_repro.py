#!/usr/bin/env python3
"""Minimal orchestration for README-first reproduction scaffolding."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List


def locale(user_language: str) -> str:
    return "zh" if user_language.lower().startswith("zh") else "en"


def text(user_language: str, en: str, zh: str) -> str:
    return zh if locale(user_language) == "zh" else en


def run_json(script: Path, args: List[str]) -> Dict[str, Any]:
    command = [sys.executable, str(script), *args]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def command_score(command: Dict[str, Any]) -> int:
    text_value = str(command.get("command", "")).lower()
    kind = command.get("kind", "run")
    score = {"run": 40, "smoke": 30, "asset": 10, "setup": 0}.get(kind, 0)

    if any(token in text_value for token in ["python ", "python3 ", "./", "whisper "]):
        score += 8
    if any(token in text_value for token in ["txt2img", "img2img", "amg.py", "transcribe", "infer", "eval"]):
        score += 8
    if "<" in text_value and ">" in text_value:
        score -= 10
    if text_value.startswith(("pip install", "conda install", "conda env create", "conda activate", "git clone", "cd ")):
        score -= 12
    return score


def choose_goal(commands: List[Dict[str, Any]]) -> Dict[str, Any]:
    for category in ["inference", "evaluation", "training", "other"]:
        candidates = [item for item in commands if item.get("category") == category]
        if not candidates:
            continue
        best = max(candidates, key=command_score)
        return {
            "selected_goal": category,
            "goal_priority": category,
            "documented_command": best.get("command", ""),
            "command_source": best.get("source", "readme"),
            "documented_command_kind": best.get("kind", "run"),
            "documented_command_section": best.get("section"),
        }

    return {
        "selected_goal": "repo-intake-only",
        "goal_priority": "other",
        "documented_command": "",
        "command_source": "none",
        "documented_command_kind": "none",
        "documented_command_section": None,
    }


def plan_skill_chain(selected_goal: str, include_analysis_pass: bool, include_paper_gap: bool) -> List[str]:
    chain = [
        "repo-intake-and-plan",
        "env-and-assets-bootstrap",
    ]
    if include_analysis_pass:
        chain.append("analyze-project")
    chain.append("run-train" if selected_goal == "training" else "minimal-run-and-audit")
    if include_paper_gap:
        chain.append("paper-context-resolver")
    return chain


def maybe_run_command(repo_path: Path, command: str, timeout: int, user_language: str) -> Dict[str, Any]:
    if not command:
        return {
            "status": "not_run",
            "documented_command_status": "not_run",
            "execution_log": [],
            "main_blocker": text(
                user_language,
                "No documented command was extracted from README.",
                "未从 README 中提取到已文档化命令。",
            ),
        }

    try:
        result = subprocess.run(
            shlex.split(command, posix=False),
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return {
            "status": "blocked",
            "documented_command_status": "blocked",
            "execution_log": [f"Command failed before launch: {exc}"],
            "main_blocker": text(
                user_language,
                f"Executable not found for documented command: {exc}",
                f"已文档化命令缺少可执行程序：{exc}",
            ),
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "partial",
            "documented_command_status": "partial",
            "execution_log": [f"Command timed out after {timeout} seconds."],
            "main_blocker": text(
                user_language,
                f"Selected documented command did not finish within {timeout} seconds.",
                f"选定的已文档化命令未在 {timeout} 秒内完成。",
            ),
        }

    combined: List[str] = []
    if result.stdout.strip():
        combined.append("STDOUT:\n" + result.stdout.strip())
    if result.stderr.strip():
        combined.append("STDERR:\n" + result.stderr.strip())

    if result.returncode == 0:
        return {
            "status": "success",
            "documented_command_status": "success",
            "execution_log": combined,
            "main_blocker": text(user_language, "None.", "无。"),
        }

    return {
        "status": "partial",
        "documented_command_status": "partial",
        "execution_log": combined,
        "main_blocker": text(
            user_language,
            f"Selected documented command exited with code {result.returncode}.",
            f"选定的已文档化命令以退出码 {result.returncode} 结束。",
        ),
    }


def build_context(
    repo_path: Path,
    scan_data: Dict[str, Any],
    command_data: Dict[str, Any],
    run_data: Dict[str, Any],
    user_language: str,
    run_selected: bool,
    include_analysis_pass: bool,
    include_paper_gap: bool,
) -> Dict[str, Any]:
    chosen = choose_goal(command_data.get("commands", []))
    skill_chain = plan_skill_chain(chosen["selected_goal"], include_analysis_pass, include_paper_gap)
    status = run_data["status"] if run_selected else "not_run"
    documented_status = (
        run_data["documented_command_status"]
        if run_selected
        else ("not_run" if not chosen["documented_command"] else "documented")
    )

    structure = scan_data.get("structure", {})
    notes: List[str] = []
    notes.extend(scan_data.get("warnings", []))
    notes.extend(command_data.get("warnings", []))
    notes.extend(run_data.get("execution_log", []))
    assumptions = [
        "README remains the primary source of truth.",
        "Environment creation should prefer conda-style isolation.",
    ]
    unverified_inferences = [
        "Environment commands are conservative placeholders until the repo confirms the exact environment name."
    ]
    protocol_deviations: List[str] = []
    human_decisions_required: List[str] = []

    if chosen["documented_command"]:
        result_summary = text(
            user_language,
            f"Selected goal `{chosen['selected_goal']}` from README evidence.",
            f"已根据 README 证据选择目标 `{chosen['selected_goal']}`。",
        )
    else:
        result_summary = text(
            user_language,
            "No documented runnable command was extracted. Repo intake was completed.",
            "未提取到可运行的已文档化命令。仓库 intake 已完成。",
        )

    if run_selected and status == "success":
        result_summary = text(
            user_language,
            "Selected documented command finished successfully.",
            "选定的已文档化命令已成功完成。",
        )
    elif run_selected and status == "partial":
        result_summary = text(
            user_language,
            "Selected documented command started but did not complete cleanly.",
            "选定的已文档化命令已启动，但未完整成功结束。",
        )
    elif run_selected and status == "blocked":
        result_summary = text(
            user_language,
            "Selected documented command could not be launched.",
            "选定的已文档化命令无法启动。",
        )

    section = chosen.get("documented_command_section")
    command_notes = [
        text(
            user_language,
            f"README path: {scan_data.get('readme_path') or 'not found'}",
            f"README 路径：{scan_data.get('readme_path') or 'not found'}",
        ),
        text(
            user_language,
            f"Detected top-level entries: {', '.join(structure.get('top_level', [])) or 'none'}",
            f"检测到的顶层条目：{', '.join(structure.get('top_level', [])) or 'none'}",
        ),
    ]
    if chosen["documented_command"]:
        source_note = text(
            user_language,
            f"Main run label: documented from README ({chosen.get('command_source', 'readme')})",
            f"主运行标签：来自 README 的 documented（{chosen.get('command_source', 'readme')}）",
        )
        if section:
            source_note += text(user_language, f", section `{section}`", f"，章节 `{section}`")
        command_notes.append(source_note)
    command_notes.append(f"Planned skill chain: {', '.join(skill_chain)}")

    if not chosen["documented_command"]:
        human_decisions_required.append(
            "Select or confirm a documented runnable command before treating this as a reproduction run."
        )
    if chosen["selected_goal"] == "training":
        human_decisions_required.append(
            "Confirm that training startup or partial verification is acceptable before claiming full training reproduction."
        )
    if run_selected and status in {"partial", "blocked"}:
        human_decisions_required.append(
            "Review the blocker before adapting commands, dependencies, or protocol-sensitive settings."
        )

    return {
        "schema_version": "1.0",
        "generated_at": scan_data.get("generated_at"),
        "user_language": user_language,
        "target_repo": str(repo_path.resolve()),
        "readme_first": True,
        "selected_goal": chosen["selected_goal"],
        "goal_priority": chosen["goal_priority"],
        "execution_skill": "run-train" if chosen["selected_goal"] == "training" else "minimal-run-and-audit",
        "planned_skill_chain": skill_chain,
        "status": status,
        "documented_command_status": documented_status,
        "documented_command": chosen["documented_command"] or "None extracted",
        "documented_command_kind": chosen.get("documented_command_kind", "none"),
        "documented_command_source": chosen.get("command_source", "none"),
        "documented_command_section": chosen.get("documented_command_section"),
        "evidence_level": "direct" if chosen["documented_command"] else "mixed",
        "result_summary": result_summary,
        "main_blocker": run_data.get("main_blocker", text(user_language, "No blocker recorded.", "未记录阻塞项。")),
        "next_action": (
            text(
                user_language,
                "Prepare environment and assets, then retry the documented command.",
                "先准备环境与资源，再重试该已文档化命令。",
            )
            if status in {"partial", "blocked", "not_run"}
            else text(
                user_language,
                "Review outputs and continue with the next documented verification step.",
                "检查输出后继续下一步已文档化验证。",
            )
        ),
        "next_safe_action": (
            "Review setup assumptions and confirm the next documented command before making any semantic changes."
            if status in {"partial", "blocked", "not_run"}
            else "Review generated outputs and confirm that the next documented verification step preserves experiment meaning."
        ),
        "setup_commands": [
            {"label": "adapted", "command": "conda env create -f environment.yml"},
            {"label": "adapted", "command": "conda activate <env-name>"},
        ],
        "asset_commands": [
            {
                "label": "inferred",
                "command": "# Add README-documented dataset and checkpoint preparation commands here.",
            }
        ],
        "run_commands": (
            [{"label": "documented", "command": chosen["documented_command"]}]
            if chosen["documented_command"]
            else []
        ),
        "verification_commands": [
            {
                "label": "inferred",
                "command": "# Add metric check, artifact check, or smoke verification command here.",
            }
        ],
        "command_notes": command_notes,
        "timeline": [
            text(user_language, "Scanned repository structure and key metadata files.", "已扫描仓库结构和关键信息文件。"),
            text(user_language, "Extracted README code blocks and shell-like commands.", "已提取 README 中的代码块和 shell 风格命令。"),
            text(
                user_language,
                f"Selected `{chosen['selected_goal']}` as the smallest trustworthy target.",
                f"已将 `{chosen['selected_goal']}` 选为最小可信目标。",
            ),
            text(
                user_language,
                "Execution step was skipped." if not run_selected else "Attempted the selected documented command.",
                "执行步骤已跳过。" if not run_selected else "已尝试选定的已文档化命令。",
            ),
        ],
        "assumptions": [
            text(user_language, "README remains the primary source of truth.", "README 仍是主要事实来源。"),
            text(user_language, "Environment creation should prefer conda-style isolation.", "环境创建应优先采用 conda 式隔离。"),
        ],
        "unverified_inferences": unverified_inferences,
        "evidence": [
            text(
                user_language,
                f"Detected files: {', '.join(scan_data.get('detected_files', [])) or 'none'}",
                f"检测到的文件：{', '.join(scan_data.get('detected_files', [])) or 'none'}",
            ),
            text(
                user_language,
                f"Command categories: {json.dumps(command_data.get('counts', {}), ensure_ascii=False)}",
                f"命令分类：{json.dumps(command_data.get('counts', {}), ensure_ascii=False)}",
            ),
            text(
                user_language,
                f"Selected command kind: {chosen.get('documented_command_kind', 'none')}",
                f"已选命令类型：{chosen.get('documented_command_kind', 'none')}",
            ),
        ],
        "blockers": [run_data.get("main_blocker", text(user_language, "None.", "无。"))],
        "protocol_deviations": protocol_deviations,
        "human_decisions_required": human_decisions_required,
        "artifact_provenance": [
            {"artifact": "readme", "source": scan_data.get("readme_path") or "not found", "kind": "repo_file"},
            {"artifact": "documented_command", "source": chosen.get("command_source", "none"), "kind": "readme_extraction"},
            {"artifact": "output_dir", "source": "repro_outputs/", "kind": "generated"},
        ],
        "notes": notes,
        "patches_applied": False,
        "patch_branch": "",
        "readme_fidelity": "preserved",
        "highest_patch_risk": "low",
        "verified_commits": [],
        "validation_summary": "",
        "patch_notes": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a minimal README-first reproduction orchestration.")
    parser.add_argument("--repo", required=True, help="Path to the target repository.")
    parser.add_argument("--output-dir", default="repro_outputs", help="Directory to write standardized outputs into.")
    parser.add_argument("--user-language", default="en", help="Language tag for human-readable reports.")
    parser.add_argument("--run-selected", action="store_true", help="Execute the selected documented command.")
    parser.add_argument("--include-analysis-pass", action="store_true", help="Include analyze-project in the planned skill chain.")
    parser.add_argument("--include-paper-gap", action="store_true", help="Include paper-context-resolver in the planned skill chain.")
    parser.add_argument("--timeout", type=int, default=120, help="Execution timeout in seconds for --run-selected.")
    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()
    base_dir = Path(__file__).resolve().parents[2]
    scan_script = base_dir / "repo-intake-and-plan" / "scripts" / "scan_repo.py"
    extract_script = base_dir / "repo-intake-and-plan" / "scripts" / "extract_commands.py"
    write_script = base_dir / "minimal-run-and-audit" / "scripts" / "write_outputs.py"

    scan_data = run_json(scan_script, ["--repo", str(repo_path), "--json"])
    readme_path = scan_data.get("readme_path")
    command_data: Dict[str, Any] = {"commands": [], "counts": {}, "warnings": []}
    if readme_path:
        command_data = run_json(extract_script, ["--readme", readme_path, "--json"])

    chosen = choose_goal(command_data.get("commands", []))
    run_data = {
        "status": "not_run",
        "documented_command_status": "not_run",
        "execution_log": [],
        "main_blocker": text(args.user_language, "Execution was not requested.", "未请求执行。"),
    }
    if args.run_selected:
        run_data = maybe_run_command(repo_path, chosen["documented_command"], args.timeout, args.user_language)

    context = build_context(
        repo_path=repo_path,
        scan_data=scan_data,
        command_data=command_data,
        run_data=run_data,
        user_language=args.user_language,
        run_selected=args.run_selected,
        include_analysis_pass=args.include_analysis_pass,
        include_paper_gap=args.include_paper_gap,
    )

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
        context_path = Path(handle.name)
        handle.write(json.dumps(context, indent=2, ensure_ascii=False))

    try:
        subprocess.run(
            [
                sys.executable,
                str(write_script),
                "--context-json",
                str(context_path),
                "--output-dir",
                str(output_dir),
            ],
            check=True,
        )
    finally:
        if context_path.exists():
            context_path.unlink()

    print(json.dumps(context, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
