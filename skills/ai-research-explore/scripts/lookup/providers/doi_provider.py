"""Free DOI metadata provider."""

from __future__ import annotations

import json
import urllib.parse
from typing import Any, Dict

from .base import coerce_author_list, http_get


def resolve_doi_record(locator_info: Dict[str, Any]) -> Dict[str, Any]:
    doi = str(locator_info.get("doi") or locator_info.get("identifier") or "").strip().lower()
    record = {
        "provider_type": "doi",
        "source_type": "paper",
        "locator_type": locator_info.get("locator_type", "doi"),
        "raw_locator": locator_info.get("raw_locator", ""),
        "normalized_id": locator_info.get("normalized_id", f"doi:{doi}"),
        "title": f"DOI:{doi}" if doi else "",
        "url": locator_info.get("url", f"https://doi.org/{doi}" if doi else ""),
        "authors": [],
        "year": None,
        "venue": "",
        "doi": doi,
        "arxiv_id": "",
        "parse_status": "parsed-only",
        "fetch_status": "parsed-only",
        "evidence_class": "parsed_locator",
        "provider_metadata": {"resolved_via": "doi"},
    }
    if not doi:
        return record
    try:
        payload = http_get(
            f"https://doi.org/{urllib.parse.quote(doi, safe='/')}",
            accept="application/vnd.citationstyles.csl+json, application/json;q=0.9",
        )
        loaded = json.loads(payload.decode("utf-8", errors="ignore"))
        title = loaded.get("title")
        if isinstance(title, list):
            title = title[0] if title else ""
        venue = loaded.get("container-title")
        if isinstance(venue, list):
            venue = venue[0] if venue else ""
        year = None
        issued = loaded.get("issued") or {}
        date_parts = issued.get("date-parts") if isinstance(issued, dict) else None
        if isinstance(date_parts, list) and date_parts and isinstance(date_parts[0], list) and date_parts[0]:
            value = date_parts[0][0]
            year = int(value) if isinstance(value, int) or (isinstance(value, str) and str(value).isdigit()) else None
        return {
            **record,
            "title": str(title or record["title"]),
            "summary": str(loaded.get("abstract") or ""),
            "authors": coerce_author_list(loaded.get("author")),
            "year": year,
            "venue": str(venue or loaded.get("publisher") or ""),
            "url": str(loaded.get("URL") or record["url"]),
            "parse_status": "resolved",
            "fetch_status": "network-fetched",
            "evidence_class": "external_provider",
            "provider_metadata": {
                "resolved_via": "doi",
                "publisher": loaded.get("publisher"),
                "type": loaded.get("type"),
            },
        }
    except Exception:
        return {**record, "parse_status": "fetch-failed", "fetch_status": "fetch-failed"}
