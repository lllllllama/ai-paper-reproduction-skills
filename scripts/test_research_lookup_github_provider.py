#!/usr/bin/env python3
"""Unit checks for the free GitHub repo provider."""

from __future__ import annotations

import base64
import importlib
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "skills" / "ai-research-explore" / "scripts"
    sys.path.insert(0, str(scripts_dir))

    github_provider = importlib.import_module("lookup.providers.github_provider")
    normalizers = importlib.import_module("lookup.normalizers")

    original_http_get_json = github_provider.http_get_json
    try:
        def fake_http_get_json(url: str, accept: str = "application/json"):
            if url.endswith("/readme"):
                return {
                    "content": base64.b64encode(
                        b"# Demo\n\nPaper: https://arxiv.org/abs/1706.03762\nDocs: https://example.com/project\n"
                    ).decode("utf-8")
                }
            return {
                "full_name": "openai/gym",
                "description": "Gym repo",
                "html_url": "https://github.com/openai/gym",
                "default_branch": "master",
                "homepage": "https://example.com/home",
                "license": {"spdx_id": "MIT"},
                "stargazers_count": 100,
            }

        github_provider.http_get_json = fake_http_get_json
        locator_info = normalizers.parse_github_repo_locator("https://github.com/openai/gym")
        record = github_provider.resolve_github_record(locator_info)
        if record["provider_type"] != "github":
            raise AssertionError("provider lost github type")
        if record["repo_full_name"] != "openai/gym":
            raise AssertionError("provider failed to parse repo_full_name")
        if record["title"] != "openai/gym":
            raise AssertionError("provider failed to parse title")
        if record["provider_metadata"]["default_branch"] != "master":
            raise AssertionError("provider lost default branch")
        if record["provider_metadata"]["homepage"] != "https://example.com/home":
            raise AssertionError("provider lost homepage")
        if "https://arxiv.org/abs/1706.03762" not in record["provider_metadata"]["paper_links_in_readme"]:
            raise AssertionError("provider failed to extract paper links from README")
        if record["parse_status"] != "resolved":
            raise AssertionError("provider should mark resolved github metadata")

        print("ok: True")
        print("checks: 7")
        print("failures: 0")
        return 0
    finally:
        github_provider.http_get_json = original_http_get_json


if __name__ == "__main__":
    raise SystemExit(main())

