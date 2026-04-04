#!/usr/bin/env python3
"""Regression checks for cache-first research lookup artifacts."""

from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "skills" / "ai-research-explore" / "scripts"
    sys.path.insert(0, str(scripts_dir))
    from passes.lookup_sources import run_lookup_pass

    temp_root = Path(tempfile.mkdtemp(prefix="codex-research-lookup-", dir=repo_root))
    try:
        repo_dir = temp_root / "repo"
        repo_dir.mkdir(parents=True, exist_ok=True)
        (repo_dir / "README.md").write_text(
            "# Demo Repo\n\n"
            "Paper: https://arxiv.org/abs/1706.03762\n"
            "Code: https://github.com/openai/gym\n"
            "Benchmark: https://example.com/leaderboard\n",
            encoding="utf-8",
        )
        sources_dir = temp_root / "sources"
        analysis_output_dir = temp_root / "analysis_outputs"
        campaign = {
            "task_family": "segmentation",
            "dataset": "DemoSeg",
            "benchmark": {"name": "DemoBench"},
            "evaluation_source": {
                "command": "python eval.py --config configs/demo.yaml",
                "path": "eval.py",
            },
            "sota_reference": [
                {"name": "DemoPaper", "metric": "miou", "value": 80.0, "source": "https://arxiv.org/abs/1706.03762"},
            ],
            "candidate_ideas": [
                {
                    "id": "idea-001",
                    "summary": "Transplant adapter block",
                    "target_component": "adapter",
                    "change_scope": "adapter_block",
                }
            ],
            "research_lookup": {
                "queries": ["segmentation adapter block", "segmentation adapter block"],
                "seed_sources": [
                    {"kind": "repo", "title": "Attention Repo", "url": "https://github.com/openai/gym"},
                    {"kind": "paper", "title": "Attention DOI", "url": "https://doi.org/10.48550/arXiv.1706.03762"},
                    {"kind": "paper", "title": "Attention DOI", "url": "https://doi.org/10.48550/arXiv.1706.03762"},
                    {"kind": "web", "title": "Example URL", "url": "https://example.com"},
                ],
            },
        }
        analysis_data = {
            "module_files": ["model.py", "trainer.py"],
            "metric_files": ["eval.py"],
        }
        code_plan = {
            "candidate_edit_targets": ["model.py", "configs/demo.yaml"],
            "source_repo_refs": [{"repo": "org/source-repo", "ref": "deadbeef", "note": "paper implementation"}],
        }

        import passes.lookup_sources as lookup_sources

        original_resolvers = (
            lookup_sources.resolve_github_record,
            lookup_sources.resolve_arxiv_record,
            lookup_sources.resolve_doi_record,
            lookup_sources.resolve_url_record,
        )
        lookup_sources.resolve_github_record = lambda locator_info: {
            "provider_type": "github",
            "source_type": "repo",
            "locator_type": locator_info["locator_type"],
            "normalized_id": locator_info["normalized_id"],
            "title": "openai/gym",
            "summary": "GitHub provider fixture",
            "url": locator_info["url"],
            "repo_full_name": "openai/gym",
            "parse_status": "resolved",
            "fetch_status": "network-fetched",
            "evidence_class": "external_provider",
            "provider_metadata": {"default_branch": "master"},
        }
        lookup_sources.resolve_arxiv_record = lambda locator_info: {
            "provider_type": "arxiv",
            "source_type": "paper",
            "locator_type": locator_info["locator_type"],
            "normalized_id": locator_info["normalized_id"],
            "title": "Attention Is All You Need",
            "summary": "arXiv provider fixture",
            "url": locator_info["url"],
            "authors": ["A. Author"],
            "year": 2017,
            "venue": "arXiv",
            "arxiv_id": locator_info["arxiv_id"],
            "parse_status": "fetch-failed",
            "fetch_status": "fetch-failed",
            "evidence_class": "parsed_locator",
            "provider_metadata": {},
        }
        lookup_sources.resolve_doi_record = lambda locator_info: {
            "provider_type": "doi",
            "source_type": "paper",
            "locator_type": locator_info["locator_type"],
            "normalized_id": locator_info["normalized_id"],
            "title": "DOI Fixture",
            "summary": "doi fixture",
            "url": locator_info["url"],
            "doi": locator_info["doi"],
            "parse_status": "resolved",
            "fetch_status": "network-fetched",
            "evidence_class": "external_provider",
            "provider_metadata": {},
        }
        lookup_sources.resolve_url_record = lambda locator_info: {
            "provider_type": "url",
            "source_type": "web",
            "locator_type": locator_info["locator_type"],
            "normalized_id": locator_info["normalized_id"],
            "title": "Example",
            "summary": "generic url fixture",
            "url": locator_info["url"],
            "venue": "example.com",
            "parse_status": "fetch-failed",
            "fetch_status": "fetch-failed",
            "evidence_class": "parsed_locator",
            "provider_metadata": {"host": "example.com"},
        }

        first = run_lookup_pass(
            sources_dir=sources_dir,
            repo_path=repo_dir,
            analysis_output_dir=analysis_output_dir,
            campaign=campaign,
            analysis_data=analysis_data,
            code_plan=code_plan,
        )
        second = run_lookup_pass(
            sources_dir=sources_dir,
            repo_path=repo_dir,
            analysis_output_dir=analysis_output_dir,
            campaign=campaign,
            analysis_data=analysis_data,
            code_plan=code_plan,
        )

        if first["sources_dir"] != str(sources_dir):
            raise AssertionError("lookup pass lost sources_dir")
        if first["index_path"] != second["index_path"]:
            raise AssertionError("lookup pass produced unstable index paths")
        if len(first["records"]) != len(second["records"]):
            raise AssertionError("lookup pass produced unstable record counts")
        if len(first["records"]) < 8:
            raise AssertionError("lookup pass did not expand enough seed records")

        seen_ids = [item["source_id"] for item in first["records"]]
        if seen_ids != [item["source_id"] for item in second["records"]]:
            raise AssertionError("lookup pass produced unstable source ids")
        if len(seen_ids) != len(set(seen_ids)):
            raise AssertionError("lookup pass did not dedupe duplicate records")
        provider_types = {item["provider_type"] for item in first["records"]}
        if "github" not in provider_types:
            raise AssertionError("lookup pass did not recognize GitHub providers")
        if "arxiv" not in provider_types and "doi" not in provider_types:
            raise AssertionError("lookup pass did not recognize arXiv/DOI providers")
        if "url" not in provider_types:
            raise AssertionError("lookup pass did not recognize generic URL providers")
        evidence_classes = {item["evidence_class"] for item in first["records"]}
        if "external_provider" not in evidence_classes:
            raise AssertionError("lookup pass did not mark external provider evidence")
        if "seed_only" not in evidence_classes:
            raise AssertionError("lookup pass did not preserve seed-only evidence classification")
        if "repo_local_extracted" not in evidence_classes:
            raise AssertionError("lookup pass did not preserve repo-local extracted evidence")
        if "parsed_locator" not in evidence_classes:
            raise AssertionError("lookup pass did not preserve parsed-locator evidence")
        if not any(item["fetch_status"] in {"network-fetched", "fetch-failed"} for item in first["records"] if item["provider_type"] in {"github", "arxiv", "doi", "url"}):
            raise AssertionError("lookup pass did not attempt provider resolution")

        name_re = re.compile(r"^[a-z]+__[a-z0-9-]+__[0-9a-f]{12}\.json$")
        for item in first["records"]:
            artifact_path = Path(item["artifact_abspath"])
            if not artifact_path.exists():
                raise AssertionError(f"lookup pass did not write {artifact_path.name}")
            if artifact_path.parent.name != "records":
                raise AssertionError("lookup pass did not move source records into sources/records")
            if not name_re.fullmatch(artifact_path.name):
                raise AssertionError(f"lookup pass wrote unstable file name {artifact_path.name}")

        index = json.loads((sources_dir / "index.json").read_text(encoding="utf-8"))
        if index["mode"] != "free-first-cache-first":
            raise AssertionError("lookup index lost free-first cache-first mode")
        if len(index["records"]) != len(first["records"]):
            raise AssertionError("lookup index lost record entries")
        if not any(item["provider_type"] == "github" for item in index["records"]):
            raise AssertionError("lookup index lost provider metadata")
        if not all("evidence_class" in item and "evidence_weight" in item for item in index["records"]):
            raise AssertionError("lookup index lost evidence classification metadata")
        if "SUMMARY.md" not in {path.name for path in sources_dir.iterdir()}:
            raise AssertionError("lookup pass did not write SUMMARY.md")
        if not (analysis_output_dir / "SOURCE_INVENTORY.md").exists():
            raise AssertionError("lookup pass did not emit SOURCE_INVENTORY.md")
        if not (analysis_output_dir / "SOURCE_SUPPORT.json").exists():
            raise AssertionError("lookup pass did not emit SOURCE_SUPPORT.json")
        if first["cache_hits"] != 0:
            raise AssertionError("first lookup run should not report cache hits")
        if second["cache_hits"] <= 0:
            raise AssertionError("second lookup run should report cache hits")

        print("ok: True")
        print("checks: 23")
        print("failures: 0")
        return 0
    finally:
        try:
            lookup_sources.resolve_github_record, lookup_sources.resolve_arxiv_record, lookup_sources.resolve_doi_record, lookup_sources.resolve_url_record = original_resolvers
        except UnboundLocalError:
            pass
        if temp_root.exists():
            shutil.rmtree(temp_root)


if __name__ == "__main__":
    raise SystemExit(main())

