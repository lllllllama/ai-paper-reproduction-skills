#!/usr/bin/env python3
"""Regression checks for source inventory rendering."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "skills" / "research-explore" / "scripts"
    sys.path.insert(0, str(scripts_dir))
    from lookup.inventory_writer import write_source_inventory
    from lookup.source_support import write_source_support

    temp_root = Path(tempfile.mkdtemp(prefix="codex-source-inventory-", dir=repo_root))
    try:
        analysis_output_dir = temp_root / "analysis_outputs"
        analysis_output_dir.mkdir(parents=True, exist_ok=True)
        records = [
            {"source_id": "paper:aaa11111", "source_type": "paper", "provider_type": "arxiv", "title": "Paper", "evidence_class": "external_provider"},
            {"source_id": "repo:bbb22222", "source_type": "repo", "provider_type": "github", "title": "Repo", "evidence_class": "parsed_locator"},
        ]
        repo_local = [{"raw_locator": "https://example.com/project", "extracted_from_repo_paths": ["README.md"]}]
        inventory_path = write_source_inventory(
            analysis_output_dir,
            records=records,
            repo_local_extractions=repo_local,
            cache_stats={"cache_hits": 1, "cache_misses": 2, "merge_upgrades": 0},
        )
        support_path = write_source_support(
            analysis_output_dir,
            {
                "schema_version": "1.0",
                "records": records,
                "records_by_evidence_class": {"external_provider": ["paper:aaa11111"]},
            },
        )
        inventory_text = inventory_path.read_text(encoding="utf-8")
        if "Source Inventory" not in inventory_text:
            raise AssertionError("inventory writer lost title")
        if "`external_provider`: 1" not in inventory_text:
            raise AssertionError("inventory writer lost evidence breakdown")
        if "README.md" not in inventory_text:
            raise AssertionError("inventory writer lost repo-local extraction provenance")
        support_payload = json.loads(support_path.read_text(encoding="utf-8"))
        if support_payload["records"][0]["source_id"] != "paper:aaa11111":
            raise AssertionError("source support writer lost record payload")

        print("ok: True")
        print("checks: 4")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())
