#!/usr/bin/env python3
"""Extract shell-like commands from README content and classify them."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List


CODE_BLOCK_RE = re.compile(r"```(?P<lang>[^\n`]*)\n(?P<body>.*?)```", re.DOTALL | re.IGNORECASE)
INLINE_CMD_RE = re.compile(r"^\s*(?:\$|>|PS> )\s*(.+)$")
COMMAND_PREFIXES = (
    "python ",
    "python3 ",
    "pip ",
    "pip3 ",
    "conda ",
    "bash ",
    "sh ",
    "chmod ",
    "export ",
    "set ",
    "CUDA_VISIBLE_DEVICES=",
    "./",
    "accelerate ",
    "torchrun ",
    "deepspeed ",
    "make ",
    "docker ",
)


def classify(command: str) -> str:
    lowered = command.lower()
    if any(word in lowered for word in ["infer", "inference", "predict", "generate", "sample", "demo"]):
        return "inference"
    if any(word in lowered for word in ["eval", "evaluate", "validation", "validate", "benchmark", "score"]):
        return "evaluation"
    if any(word in lowered for word in ["train", "training", "finetune", "fine-tune", "pretrain", "pre-train"]):
        return "training"
    return "other"


def looks_like_command(line: str) -> bool:
    candidate = re.sub(r"^(?:\$|PS> )\s*", "", line.strip())
    if not candidate or candidate.startswith("#"):
        return False
    if candidate.startswith(("python", "pip", "conda", "bash", "sh", "make", "docker")):
        return True
    if candidate.startswith(COMMAND_PREFIXES):
        return True
    if re.search(r"\s--[A-Za-z0-9_-]+", candidate):
        return True
    if re.search(r"\b(?:python|pip|conda|torchrun|deepspeed|accelerate|bash|sh)\b", candidate):
        return True
    if re.search(r"[\\/].+\.(?:py|sh|bat)", candidate):
        return True
    if candidate.startswith(("cd ", "ls ", "mkdir ", "wget ", "curl ", "git ")):
        return True
    return False


def clean_lines(block: str) -> List[str]:
    commands: List[str] = []
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if not looks_like_command(line):
            continue
        line = re.sub(r"^(?:\$|PS> )\s*", "", line)
        commands.append(line)
    return commands


def extract_commands(readme_text: str) -> Dict[str, object]:
    commands: List[Dict[str, str]] = []
    warnings: List[str] = []
    seen = set()

    for match in CODE_BLOCK_RE.finditer(readme_text):
        lang = (match.group("lang") or "").strip().lower()
        if lang and lang not in {"bash", "shell", "sh", "zsh", "powershell", "cmd"}:
            continue

        lines = clean_lines(match.group("body"))
        if not lines:
            continue

        for line in lines:
            if line not in seen:
                commands.append({"command": line, "category": classify(line), "source": "code_block"})
                seen.add(line)

    for line in readme_text.splitlines():
        matched = INLINE_CMD_RE.match(line)
        if not matched:
            continue
        command = matched.group(1).strip()
        if not looks_like_command(command):
            continue
        if command and command not in seen:
            commands.append({"command": command, "category": classify(command), "source": "inline"})
            seen.add(command)

    if not commands:
        warnings.append("No shell-like commands were extracted from the README.")

    counts: Dict[str, int] = {}
    for item in commands:
        category = item["category"]
        counts[category] = counts.get(category, 0) + 1

    return {
        "commands": commands,
        "counts": counts,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract shell-like commands from a README.")
    parser.add_argument("--readme", required=True, help="Path to the README file.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()

    readme_path = Path(args.readme)
    text = readme_path.read_text(encoding="utf-8", errors="replace")
    data = extract_commands(text)

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        for item in data["commands"]:
            print(f"[{item['category']}] {item['command']}")
        if data["warnings"]:
            print("Warnings:")
            for warning in data["warnings"]:
                print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
