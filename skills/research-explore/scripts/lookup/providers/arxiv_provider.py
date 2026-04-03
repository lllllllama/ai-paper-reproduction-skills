"""Free arXiv metadata provider."""

from __future__ import annotations

import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any, Dict

from .base import http_get


def resolve_arxiv_record(locator_info: Dict[str, Any]) -> Dict[str, Any]:
    arxiv_id = str(locator_info.get("arxiv_id") or locator_info.get("identifier") or "").strip()
    record = {
        "provider_type": "arxiv",
        "source_type": "paper",
        "locator_type": locator_info.get("locator_type", "arxiv_id"),
        "raw_locator": locator_info.get("raw_locator", ""),
        "normalized_id": locator_info.get("normalized_id", f"arxiv:{arxiv_id.lower()}"),
        "title": f"arXiv:{arxiv_id}" if arxiv_id else "",
        "url": locator_info.get("url", ""),
        "authors": [],
        "year": None,
        "venue": "arXiv",
        "doi": "",
        "arxiv_id": arxiv_id,
        "parse_status": "parsed-only",
        "fetch_status": "parsed-only",
        "evidence_class": "parsed_locator",
        "provider_metadata": {"resolved_via": "arxiv"},
    }
    if not arxiv_id:
        return record
    try:
        payload = http_get(
            f"https://export.arxiv.org/api/query?id_list={urllib.parse.quote(arxiv_id)}",
            accept="application/atom+xml, text/xml;q=0.9",
        )
        root = ET.fromstring(payload.decode("utf-8", errors="ignore"))
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        entry = root.find("atom:entry", namespace)
        if entry is None:
            return {**record, "parse_status": "fetch-failed", "fetch_status": "fetch-failed"}
        authors = [
            (node.findtext("atom:name", default="", namespaces=namespace) or "").strip()
            for node in entry.findall("atom:author", namespace)
            if (node.findtext("atom:name", default="", namespaces=namespace) or "").strip()
        ]
        published = (entry.findtext("atom:published", default="", namespaces=namespace) or "").strip()
        year = int(published[:4]) if published[:4].isdigit() else None
        url = record["url"]
        for item in entry.findall("atom:link", namespace):
            href = item.attrib.get("href", "")
            if href:
                url = href
                break
        return {
            **record,
            "title": (entry.findtext("atom:title", default="", namespaces=namespace) or "").strip() or record["title"],
            "summary": (entry.findtext("atom:summary", default="", namespaces=namespace) or "").strip(),
            "authors": authors,
            "year": year,
            "url": url,
            "parse_status": "resolved",
            "fetch_status": "network-fetched",
            "evidence_class": "external_provider",
        }
    except Exception:
        return {**record, "parse_status": "fetch-failed", "fetch_status": "fetch-failed"}
