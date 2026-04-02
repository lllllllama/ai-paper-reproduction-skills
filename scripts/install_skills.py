#!/usr/bin/env python3
"""Install this repository's skill folders into a Codex or Claude Code skills directory."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path
from typing import Iterable, List, Mapping


def default_target(client: str, env: Mapping[str, str] | None = None, home: Path | None = None) -> Path:
    env_map = os.environ if env is None else env
    home_path = (home or Path.home()).expanduser()

    if client == "codex":
        codex_home = env_map.get("CODEX_HOME")
        base = Path(codex_home).expanduser() if codex_home else home_path / ".codex"
        return (base / "skills").resolve()

    if client == "claude":
        claude_home = env_map.get("CLAUDE_HOME")
        base = Path(claude_home).expanduser() if claude_home else home_path / ".claude"
        return (base / "skills").resolve()

    raise ValueError(f"Unsupported client: {client}")


def discover_skills(skills_root: Path) -> List[Path]:
    return sorted(
        path for path in skills_root.iterdir()
        if path.is_dir() and (path / "SKILL.md").exists()
    )


def safe_remove(path: Path, root: Path) -> None:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    if resolved_root not in resolved_path.parents:
        raise ValueError(f"Refusing to remove path outside target root: {resolved_path}")
    if resolved_path.exists():
        if resolved_path.is_symlink() or resolved_path.is_file():
            resolved_path.unlink()
        else:
            shutil.rmtree(resolved_path)


def copy_skill(source: Path, target: Path) -> None:
    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
        dirs_exist_ok=False,
    )


def install_skills(
    repo_root: Path,
    target_root: Path,
    mode: str,
    force: bool,
) -> List[Path]:
    skills_root = repo_root / "skills"
    skill_dirs = discover_skills(skills_root)
    target_root.mkdir(parents=True, exist_ok=True)

    installed: List[Path] = []
    for skill_dir in skill_dirs:
        target_path = target_root / skill_dir.name
        if target_path.exists() or target_path.is_symlink():
            if not force:
                raise FileExistsError(
                    f"Target already exists: {target_path}. Re-run with --force to replace it."
                )
            safe_remove(target_path, target_root)

        if mode == "copy":
            copy_skill(skill_dir, target_path)
        else:
            target_path.symlink_to(skill_dir.resolve(), target_is_directory=True)

        installed.append(target_path)

    return installed


def format_paths(paths: Iterable[Path]) -> str:
    return "\n".join(f"- {path}" for path in paths)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install all skill folders into a Codex or Claude Code skills directory.")
    parser.add_argument(
        "--client",
        choices=["codex", "claude"],
        default="codex",
        help="Which agent client to target. Defaults to Codex for backward compatibility.",
    )
    parser.add_argument(
        "--target",
        default=None,
        help="Override the skills directory. Defaults to CODEX_HOME/skills or ~/.codex/skills for Codex, and CLAUDE_HOME/skills or ~/.claude/skills for Claude Code.",
    )
    parser.add_argument(
        "--mode",
        choices=["copy", "symlink"],
        default="copy",
        help="Installation mode. Use symlink for local development, copy for portable installs.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing target skill folders.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    target_root = (
        Path(args.target).expanduser().resolve()
        if args.target
        else default_target(args.client)
    )
    installed = install_skills(repo_root, target_root, args.mode, args.force)

    print(f"Installed {len(installed)} skills to {target_root} for {args.client}")
    print(format_paths(installed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
