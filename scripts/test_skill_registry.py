#!/usr/bin/env python3
"""Validate the machine-readable skill registry."""

from __future__ import annotations

import json
from pathlib import Path


ALLOWED_TIERS = {"public", "helper"}
ALLOWED_LANES = {"trusted", "explore", "helper"}


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    registry_path = repo_root / "references" / "skill-registry.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))

    if payload.get("schema_version") != "1.0":
        raise AssertionError("skill registry schema_version must be `1.0`")

    skills = payload.get("skills", [])
    if not isinstance(skills, list) or not skills:
        raise AssertionError("skill registry must contain a non-empty `skills` list")

    names = set()
    for item in skills:
        name = item.get("name")
        if not name or not isinstance(name, str):
            raise AssertionError("each skill registry entry must have a string `name`")
        if name in names:
            raise AssertionError(f"duplicate skill registry entry: {name}")
        names.add(name)

        if item.get("tier") not in ALLOWED_TIERS:
            raise AssertionError(f"{name} has invalid tier: {item.get('tier')}")
        if item.get("lane") not in ALLOWED_LANES:
            raise AssertionError(f"{name} has invalid lane: {item.get('lane')}")

        compat = item.get("compat", {})
        if "preserve_name" not in compat:
            raise AssertionError(f"{name} is missing compat.preserve_name")
        if not isinstance(compat.get("aliases", []), list):
            raise AssertionError(f"{name} has invalid compat.aliases")
        if name == "ai-research-reproduction" and "ai-paper-reproduction" not in compat.get("aliases", []):
            raise AssertionError("ai-research-reproduction must preserve ai-paper-reproduction as a compat alias")
        if name == "ai-research-explore" and "research-explore" not in compat.get("aliases", []):
            raise AssertionError("ai-research-explore must preserve research-explore as a compat alias")

        can_call = item.get("can_call", [])
        if not isinstance(can_call, list):
            raise AssertionError(f"{name} has invalid can_call list")

        output_mode = item.get("output_mode", {})
        if "kind" not in output_mode:
            raise AssertionError(f"{name} is missing output_mode.kind")
        if "artifacts" not in output_mode or not isinstance(output_mode["artifacts"], list):
            raise AssertionError(f"{name} has invalid output_mode.artifacts")

        skill_root = repo_root / "skills" / name
        if not skill_root.exists():
            raise AssertionError(f"{name} is registered but missing from skills/")

        for rel in item.get("required_files", []):
            if not (skill_root / rel).exists():
                raise AssertionError(f"{name} is missing required file declared in registry: {rel}")

    for item in skills:
        for callee in item.get("can_call", []):
            if callee not in names:
                raise AssertionError(f"{item['name']} references unknown callee `{callee}`")

    print("ok: True")
    print(f"skills: {len(skills)}")
    print("failures: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
