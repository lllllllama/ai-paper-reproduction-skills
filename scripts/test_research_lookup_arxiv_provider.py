#!/usr/bin/env python3
"""Unit checks for the free arXiv provider."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "skills" / "ai-research-explore" / "scripts"
    sys.path.insert(0, str(scripts_dir))

    arxiv_provider = importlib.import_module("lookup.providers.arxiv_provider")
    normalizers = importlib.import_module("lookup.normalizers")

    original_http_get = arxiv_provider.http_get
    try:
        arxiv_provider.http_get = lambda url, accept=None: (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<feed xmlns="http://www.w3.org/2005/Atom">'
            b"<entry>"
            b"<title>Attention Is All You Need</title>"
            b"<summary>Transformer abstract.</summary>"
            b"<published>2017-06-12T00:00:00Z</published>"
            b'<author><name>Alice Example</name></author>'
            b'<author><name>Bob Example</name></author>'
            b'<link href="https://arxiv.org/abs/1706.03762"/>'
            b"</entry>"
            b"</feed>"
        )
        locator_info = normalizers.parse_arxiv_locator("https://arxiv.org/abs/1706.03762")
        record = arxiv_provider.resolve_arxiv_record(locator_info)
        if record["provider_type"] != "arxiv":
            raise AssertionError("provider lost arxiv type")
        if record["source_type"] != "paper":
            raise AssertionError("provider lost paper source_type")
        if record["locator_type"] != "arxiv_url":
            raise AssertionError("provider lost arxiv locator_type")
        if record["normalized_id"] != "arxiv:1706.03762":
            raise AssertionError("provider lost normalized arxiv id")
        if record["title"] != "Attention Is All You Need":
            raise AssertionError("provider failed to parse arxiv title")
        if record["authors"] != ["Alice Example", "Bob Example"]:
            raise AssertionError("provider failed to parse arxiv authors")
        if record["year"] != 2017:
            raise AssertionError("provider failed to parse arxiv year")
        if record["parse_status"] != "resolved":
            raise AssertionError("provider should mark resolved arxiv metadata")

        print("ok: True")
        print("checks: 8")
        print("failures: 0")
        return 0
    finally:
        arxiv_provider.http_get = original_http_get


if __name__ == "__main__":
    raise SystemExit(main())

