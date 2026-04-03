"""Free GitHub repository metadata provider."""

from __future__ import annotations

import base64
from typing import Any, Dict, List

from lookup.normalizers import extract_urls

from .base import http_get_json


def _paper_links(links: List[str]) -> List[str]:
    return [
        link
        for link in links
        if "arxiv.org" in link.lower() or "doi.org" in link.lower() or "openreview.net" in link.lower()
    ]


def _fetch_readme(owner: str, repo: str) -> Dict[str, Any]:
    try:
        payload = http_get_json(f"https://api.github.com/repos/{owner}/{repo}/readme")
    except Exception:
        return {"readme_links": [], "paper_links_in_readme": []}
    content = payload.get("content")
    if not content:
        return {"readme_links": [], "paper_links_in_readme": []}
    try:
        decoded = base64.b64decode(str(content).encode("utf-8"), validate=False).decode("utf-8", errors="ignore")
    except Exception:
        return {"readme_links": [], "paper_links_in_readme": []}
    links = extract_urls(decoded)
    return {
        "readme_links": links,
        "paper_links_in_readme": _paper_links(links),
    }


def resolve_github_record(locator_info: Dict[str, Any]) -> Dict[str, Any]:
    repo_full_name = str(locator_info.get("repo_full_name") or locator_info.get("identifier") or "").strip()
    owner = str(locator_info.get("owner") or "").strip()
    repo = str(locator_info.get("repo") or "").strip()
    record = {
        "provider_type": "github",
        "source_type": "repo",
        "locator_type": locator_info.get("locator_type", "github_repo_url"),
        "raw_locator": locator_info.get("raw_locator", ""),
        "normalized_id": locator_info.get("normalized_id", f"github:{repo_full_name.lower()}"),
        "title": repo_full_name,
        "url": locator_info.get("url", ""),
        "authors": [],
        "year": None,
        "venue": "GitHub",
        "repo_full_name": repo_full_name,
        "doi": "",
        "arxiv_id": "",
        "source_file": locator_info.get("source_file", ""),
        "parse_status": "parsed-only",
        "fetch_status": "parsed-only",
        "evidence_class": "parsed_locator",
        "provider_metadata": {"resolved_via": "github"},
    }
    if not owner or not repo:
        return record
    try:
        payload = http_get_json(f"https://api.github.com/repos/{owner}/{repo}")
        readme_meta = _fetch_readme(owner, repo)
        return {
            **record,
            "title": str(payload.get("full_name") or record["title"]),
            "summary": str(payload.get("description") or ""),
            "url": str(payload.get("html_url") or record["url"]),
            "repo_full_name": str(payload.get("full_name") or repo_full_name),
            "parse_status": "resolved",
            "fetch_status": "network-fetched",
            "evidence_class": "external_provider",
            "provider_metadata": {
                "resolved_via": "github",
                "default_branch": payload.get("default_branch"),
                "homepage": payload.get("homepage"),
                "license": (payload.get("license") or {}).get("spdx_id"),
                "stargazers_count": payload.get("stargazers_count"),
                **readme_meta,
            },
        }
    except Exception:
        return {**record, "parse_status": "fetch-failed", "fetch_status": "fetch-failed"}
