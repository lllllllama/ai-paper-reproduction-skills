#!/usr/bin/env python3
"""Unit checks for the generic URL provider."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "skills" / "research-explore" / "scripts"
    sys.path.insert(0, str(scripts_dir))

    url_provider = importlib.import_module("lookup.providers.url_provider")
    normalizers = importlib.import_module("lookup.normalizers")

    original_http_get = url_provider.http_get
    try:
        url_provider.http_get = lambda url, accept=None: (
            b"<html><head>"
            b"<title>Example Title</title>"
            b'<meta name="description" content="Example description.">'
            b'<link rel="canonical" href="https://example.com/canonical">'
            b"</head><body></body></html>"
        )
        locator_info = normalizers.parse_generic_url("https://example.com/demo?x=1")
        record = url_provider.resolve_url_record(locator_info)
        if record["provider_type"] != "url":
            raise AssertionError("provider lost url type")
        if record["title"] != "Example Title":
            raise AssertionError("provider failed to parse title")
        if record["summary"] != "Example description.":
            raise AssertionError("provider failed to parse description")
        if record["url"] != "https://example.com/canonical":
            raise AssertionError("provider failed to parse canonical url")
        if record["provider_metadata"]["host"] != "example.com":
            raise AssertionError("provider lost host metadata")
        if record["parse_status"] != "resolved":
            raise AssertionError("provider should mark resolved generic url metadata")

        print("ok: True")
        print("checks: 6")
        print("failures: 0")
        return 0
    finally:
        url_provider.http_get = original_http_get


if __name__ == "__main__":
    raise SystemExit(main())
