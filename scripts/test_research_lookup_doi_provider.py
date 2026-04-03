#!/usr/bin/env python3
"""Unit checks for the free DOI provider."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "skills" / "research-explore" / "scripts"
    sys.path.insert(0, str(scripts_dir))

    doi_provider = importlib.import_module("lookup.providers.doi_provider")
    normalizers = importlib.import_module("lookup.normalizers")

    original_http_get = doi_provider.http_get
    try:
        doi_provider.http_get = lambda url, accept=None: (
            b'{"title":"Paper Title","abstract":"Paper abstract.","container-title":"NeurIPS",'
            b'"issued":{"date-parts":[[2023]]},"author":[{"given":"Alice","family":"Smith"}],'
            b'"URL":"https://doi.org/10.1234/demo","publisher":"Test Pub","type":"proceedings-article"}'
        )
        locator_info = normalizers.parse_doi_locator("10.1234/DEMO")
        record = doi_provider.resolve_doi_record(locator_info)
        if record["provider_type"] != "doi":
            raise AssertionError("provider lost doi type")
        if record["normalized_id"] != "doi:10.1234/demo":
            raise AssertionError("provider failed to normalize doi")
        if record["title"] != "Paper Title":
            raise AssertionError("provider failed to parse doi title")
        if record["authors"] != ["Alice Smith"]:
            raise AssertionError("provider failed to parse doi authors")
        if record["venue"] != "NeurIPS":
            raise AssertionError("provider failed to parse venue")
        if record["year"] != 2023:
            raise AssertionError("provider failed to parse year")
        if record["doi"] != "10.1234/demo":
            raise AssertionError("provider lost doi field")
        if record["parse_status"] != "resolved":
            raise AssertionError("provider should mark resolved doi metadata")

        print("ok: True")
        print("checks: 8")
        print("failures: 0")
        return 0
    finally:
        doi_provider.http_get = original_http_get


if __name__ == "__main__":
    raise SystemExit(main())
