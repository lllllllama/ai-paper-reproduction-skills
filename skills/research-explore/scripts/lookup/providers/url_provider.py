"""Generic URL metadata provider."""

from __future__ import annotations

import urllib.parse
from typing import Any, Dict

from lookup.normalizers import canonicalize_url

from .base import MetadataHTMLParser, http_get


def resolve_url_record(locator_info: Dict[str, Any]) -> Dict[str, Any]:
    url = canonicalize_url(locator_info.get("url") or locator_info.get("raw_locator") or "")
    parsed = urllib.parse.urlsplit(url) if url else None
    record = {
        "provider_type": "url",
        "source_type": "web",
        "locator_type": locator_info.get("locator_type", "url"),
        "raw_locator": locator_info.get("raw_locator", ""),
        "normalized_id": locator_info.get("normalized_id", f"url:{url}" if url else ""),
        "title": url,
        "url": url,
        "authors": [],
        "year": None,
        "venue": parsed.netloc if parsed else "",
        "repo_full_name": "",
        "doi": "",
        "arxiv_id": "",
        "parse_status": "parsed-only",
        "fetch_status": "parsed-only",
        "evidence_class": "parsed_locator",
        "provider_metadata": {"resolved_via": "url", "host": parsed.netloc.lower() if parsed else ""},
    }
    if not url:
        return record
    try:
        payload = http_get(url, accept="text/html, application/xhtml+xml;q=0.9")
        parser = MetadataHTMLParser()
        parser.feed(payload.decode("utf-8", errors="ignore"))
        canonical = parser.canonical_url() or url
        return {
            **record,
            "title": parser.meta.get("og:title") or parser.title_text() or url,
            "summary": parser.description_text(),
            "url": canonicalize_url(canonical),
            "parse_status": "resolved",
            "fetch_status": "network-fetched",
            "evidence_class": "external_provider",
            "provider_metadata": {
                **record["provider_metadata"],
                "canonical_url": canonicalize_url(canonical),
            },
        }
    except Exception:
        return {**record, "parse_status": "fetch-failed", "fetch_status": "fetch-failed"}
