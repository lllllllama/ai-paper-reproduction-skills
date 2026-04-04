#!/usr/bin/env python3
"""Unit checks for repo-local source extraction."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "skills" / "ai-research-explore" / "scripts"
    sys.path.insert(0, str(scripts_dir))
    from lookup.repo_extractors import extract_repo_local_seeds

    temp_root = Path(tempfile.mkdtemp(prefix="codex-repo-extract-", dir=repo_root))
    try:
        repo_dir = temp_root / "repo"
        (repo_dir / "docs").mkdir(parents=True, exist_ok=True)
        (repo_dir / "configs").mkdir(parents=True, exist_ok=True)
        (repo_dir / "README.md").write_text(
            "# Demo\n\nPaper: https://arxiv.org/abs/1706.03762\nCode: https://github.com/openai/gym\n",
            encoding="utf-8",
        )
        (repo_dir / "docs" / "notes.md").write_text(
            "Benchmark: https://example.com/leaderboard\nDOI: 10.1234/demo\n",
            encoding="utf-8",
        )
        (repo_dir / "configs" / "demo.yaml").write_text("# Project page https://example.com/project\nmodel: demo\n", encoding="utf-8")

        seeds = extract_repo_local_seeds(repo_dir)
        locators = {item["raw_locator"] for item in seeds}
        if "https://arxiv.org/abs/1706.03762" not in locators:
            raise AssertionError("repo extractor missed arXiv link")
        if "https://github.com/openai/gym" not in locators:
            raise AssertionError("repo extractor missed GitHub repo link")
        if "https://example.com/leaderboard" not in locators:
            raise AssertionError("repo extractor missed benchmark link")
        if "10.1234/demo" not in {item["raw_locator"].lower() for item in seeds}:
            raise AssertionError("repo extractor missed DOI locator")
        if not all(item["origin"] == "repo_local_extracted" for item in seeds):
            raise AssertionError("repo extractor lost repo-local evidence origin")
        if not any("README.md" in item["extracted_from_repo_paths"][0] for item in seeds):
            raise AssertionError("repo extractor lost source path provenance")

        print("ok: True")
        print("checks: 6")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())

