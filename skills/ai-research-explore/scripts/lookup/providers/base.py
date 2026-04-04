"""Shared transport and HTML helpers for lookup providers."""

from __future__ import annotations

import json
import urllib.request
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple


REQUEST_TIMEOUT_SECONDS = 6
USER_AGENT = "ai-research-explore-lookup/2.0"


class MetadataHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title_parts: List[str] = []
        self.meta: Dict[str, str] = {}
        self.links: Dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        lowered = tag.lower()
        attr_map = {key.lower(): (value or "") for key, value in attrs}
        if lowered == "title":
            self.in_title = True
        if lowered == "meta":
            name = attr_map.get("name") or attr_map.get("property")
            content = attr_map.get("content", "").strip()
            if name and content:
                self.meta[name.lower()] = content
        if lowered == "link":
            rel = attr_map.get("rel", "").lower()
            href = attr_map.get("href", "").strip()
            if rel and href:
                self.links[rel] = href

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title and data.strip():
            self.title_parts.append(data.strip())

    def title_text(self) -> str:
        return " ".join(self.title_parts).strip()

    def description_text(self) -> str:
        for key in ("og:description", "description", "twitter:description"):
            if self.meta.get(key):
                return self.meta[key]
        return ""

    def canonical_url(self) -> str:
        return self.links.get("canonical") or self.meta.get("og:url", "")


def http_get(url: str, *, accept: str = "application/json, text/plain;q=0.9, text/html;q=0.8") -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept,
        },
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return response.read()


def http_get_json(url: str, *, accept: str = "application/json") -> Dict[str, Any]:
    payload = http_get(url, accept=accept)
    loaded = json.loads(payload.decode("utf-8", errors="ignore"))
    return loaded if isinstance(loaded, dict) else {}


def coerce_author_list(values: Any) -> List[str]:
    authors: List[str] = []
    if isinstance(values, list):
        for item in values:
            if isinstance(item, dict):
                given = str(item.get("given") or "").strip()
                family = str(item.get("family") or "").strip()
                full = " ".join(part for part in [given, family] if part).strip()
                if full:
                    authors.append(full)
            elif str(item).strip():
                authors.append(str(item).strip())
    return authors

