#!/usr/bin/env python3
"""Validate repository structure and lightweight skill metadata."""

from __future__ import annotations

import argparse
import json
import py_compile
import re
from pathlib import Path
from typing import Dict, List, Tuple


SKILL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
REQUIRED_SKILLS = {
    "ai-paper-reproduction": {
        "files": [
            "SKILL.md",
            "references/architecture.md",
            "references/output-spec.md",
            "references/patch-policy.md",
            "references/language-policy.md",
            "assets/SUMMARY.template.md",
            "assets/COMMANDS.template.md",
            "assets/LOG.template.md",
            "assets/PATCHES.template.md",
            "assets/status.template.json",
            "scripts/orchestrate_repro.py",
            "agents/openai.yaml",
        ],
    },
    "repo-intake-and-plan": {
        "files": [
            "SKILL.md",
            "references/repo-scan-rules.md",
            "scripts/scan_repo.py",
            "scripts/extract_commands.py",
            "agents/openai.yaml",
        ],
    },
    "env-and-assets-bootstrap": {
        "files": [
            "SKILL.md",
            "references/env-policy.md",
            "references/assets-policy.md",
            "scripts/bootstrap_env.sh",
            "scripts/prepare_assets.py",
            "agents/openai.yaml",
        ],
    },
    "minimal-run-and-audit": {
        "files": [
            "SKILL.md",
            "references/reporting-policy.md",
            "scripts/write_outputs.py",
            "agents/openai.yaml",
        ],
    },
    "paper-context-resolver": {
        "files": [
            "SKILL.md",
            "references/paper-assisted-reproduction.md",
            "agents/openai.yaml",
        ],
    },
}
IGNORED_PATH_PARTS = {"tmp", "artifacts", "repro_outputs", "__pycache__", ".git"}


def parse_front_matter(skill_md: Path) -> Dict[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{skill_md} is missing YAML front matter.")

    try:
        _, front_matter, _ = text.split("---", 2)
    except ValueError as exc:
        raise ValueError(f"{skill_md} has malformed front matter.") from exc

    data: Dict[str, str] = {}
    for raw_line in front_matter.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def validate_openai_yaml(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8")
    required_keys = ["display_name:", "short_description:", "default_prompt:"]
    return [f"Missing `{key[:-1]}` in {path}" for key in required_keys if key not in text]


def validate_python_files(root: Path) -> List[str]:
    errors: List[str] = []
    for path in root.rglob("*.py"):
        if any(part in IGNORED_PATH_PARTS for part in path.parts):
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"Python compile failed for {path}: {exc.msg}")
    return errors


def validate_repo(root: Path) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    for rel in ["README.md", "CONTRIBUTING.md", ".editorconfig", "scripts/install_skills.py", "scripts/validate_repo.py"]:
        if not (root / rel).exists():
            errors.append(f"Missing repository file: {rel}")

    for rel in [
        "scripts/test_trigger_boundaries.py",
        "scripts/test_readme_selection.py",
        "scripts/test_output_rendering.py",
        "tests/trigger_cases.json",
        "tests/readme_selection_cases.json",
        "references/trigger-boundary-policy.md",
    ]:
        if not (root / rel).exists():
            errors.append(f"Missing repository file: {rel}")

    skills_root = root / "skills"
    if not skills_root.exists():
        errors.append("Missing `skills/` directory.")
        return errors, warnings

    skill_dirs = sorted(
        path for path in skills_root.iterdir()
        if path.is_dir() and (path / "SKILL.md").exists()
    )
    discovered_names = {path.name for path in skill_dirs}

    for required_name in REQUIRED_SKILLS:
        if required_name not in discovered_names:
            errors.append(f"Missing required skill directory: skills/{required_name}")

    for skill_dir in skill_dirs:
        if not SKILL_NAME_RE.match(skill_dir.name):
            errors.append(f"Invalid skill directory name: {skill_dir.name}")

        try:
            front_matter = parse_front_matter(skill_dir / "SKILL.md")
        except ValueError as exc:
            errors.append(str(exc))
            continue

        declared_name = front_matter.get("name", "")
        description = front_matter.get("description", "")
        if declared_name != skill_dir.name:
            errors.append(
                f"Front matter name mismatch for {skill_dir / 'SKILL.md'}: `{declared_name}` != `{skill_dir.name}`"
            )
        if not description:
            errors.append(f"Missing description in {skill_dir / 'SKILL.md'}")

        required_files = REQUIRED_SKILLS.get(skill_dir.name, {}).get("files", [])
        for rel in required_files:
            if not (skill_dir / rel).exists():
                errors.append(f"Missing required file for {skill_dir.name}: {rel}")

        agent_yaml = skill_dir / "agents" / "openai.yaml"
        if agent_yaml.exists():
            errors.extend(validate_openai_yaml(agent_yaml))
        else:
            warnings.append(f"No agents/openai.yaml for {skill_dir.name}")

    errors.extend(validate_python_files(root))

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate repository structure and skill metadata.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    errors, warnings = validate_repo(root)
    payload = {
        "ok": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"ok: {payload['ok']}")
        print(f"errors: {payload['error_count']}")
        print(f"warnings: {payload['warning_count']}")
        for item in errors:
            print(f"ERROR: {item}")
        for item in warnings:
            print(f"WARN: {item}")

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
