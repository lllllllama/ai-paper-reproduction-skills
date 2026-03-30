#!/usr/bin/env python3
"""Prepare a conservative asset manifest for reproduction work."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


COMMON_ASSET_DIRS = ["datasets", "data", "checkpoints", "weights", "cache", ".cache"]


def prepare_assets(repo: Path, assets_root: Path) -> Dict[str, object]:
    assets_root.mkdir(parents=True, exist_ok=True)
    manifest: List[Dict[str, str]] = []

    for name in COMMON_ASSET_DIRS:
        repo_candidate = repo / name
        target = assets_root / name
        state = "present" if repo_candidate.exists() else "missing"
        manifest.append(
            {
                "asset_group": name,
                "source_hint": str(repo_candidate.resolve()) if repo_candidate.exists() else "not found in repo",
                "target_path": str(target.resolve()),
                "status": state,
            }
        )

    output = {
        "repo_path": str(repo.resolve()),
        "assets_root": str(assets_root.resolve()),
        "manifest": manifest,
    }
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a conservative asset manifest.")
    parser.add_argument("--repo", required=True, help="Path to the target repository.")
    parser.add_argument(
        "--assets-root",
        default="artifacts/assets",
        help="Directory where prepared assets should live.",
    )
    parser.add_argument(
        "--output-json",
        default="artifacts/assets/asset_manifest.json",
        help="Path to write the manifest JSON.",
    )
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    assets_root = Path(args.assets_root).resolve()
    output_json = Path(args.output_json).resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)

    data = prepare_assets(repo, assets_root)
    output_json.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
