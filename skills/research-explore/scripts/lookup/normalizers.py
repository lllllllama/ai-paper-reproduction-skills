"""Locator parsing and normalization helpers for research lookup."""

from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
from typing import Any, Dict, Optional


ARXIV_ID_RE = re.compile(r"(?:arxiv:|arxiv\.org/(?:abs|pdf)/)?(?P<id>\d{4}\.\d{4,5}(?:v\d+)?)", re.IGNORECASE)
DOI_RE = re.compile(r"(?:https?://(?:dx\.)?doi\.org/)?(?P<doi>10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.IGNORECASE)
GITHUB_URL_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s#]+)(?:/(?P<rest>.*))?$",
    re.IGNORECASE,
)
HTTP_URL_RE = re.compile(r"^https?://", re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s<>\]\"')]+", re.IGNORECASE)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return slug[:48] or "source"


def stable_digest(payload: Dict[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def stable_filename(kind: str, slug: str, digest: str, suffix: str = "json") -> str:
    return f"{kind}__{slug}__{digest[:12]}.{suffix}"


def ensure_http_url(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if HTTP_URL_RE.match(text):
        return text
    if text.lower().startswith("doi:"):
        return f"https://doi.org/{text[4:].strip()}"
    return text


def canonicalize_url(value: str) -> str:
    text = ensure_http_url(value)
    if not text:
        return ""
    parsed = urllib.parse.urlsplit(text)
    path = parsed.path or "/"
    return urllib.parse.urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path.rstrip("/") or "/",
            parsed.query,
            "",
        )
    )


def extract_urls(text: str) -> list[str]:
    found: list[str] = []
    for match in URL_RE.finditer(str(text or "")):
        url = match.group(0).rstrip(".,);]")
        if url not in found:
            found.append(url)
    return found


def parse_arxiv_locator(locator: str) -> Optional[Dict[str, Any]]:
    text = str(locator or "").strip()
    match = ARXIV_ID_RE.search(text)
    if not match:
        return None
    arxiv_id = match.group("id")
    locator_type = "arxiv_url" if "arxiv.org" in text.lower() else "arxiv_id"
    return {
        "provider_type": "arxiv",
        "source_type": "paper",
        "locator_type": locator_type,
        "raw_locator": text,
        "normalized_id": f"arxiv:{arxiv_id.lower()}",
        "identifier": arxiv_id,
        "arxiv_id": arxiv_id,
        "url": f"https://arxiv.org/abs/{arxiv_id}",
    }


def parse_doi_locator(locator: str) -> Optional[Dict[str, Any]]:
    text = str(locator or "").strip()
    match = DOI_RE.search(text)
    if not match:
        return None
    doi = match.group("doi").lower()
    locator_type = "doi_url" if "doi.org" in text.lower() else "doi"
    return {
        "provider_type": "doi",
        "source_type": "paper",
        "locator_type": locator_type,
        "raw_locator": text,
        "normalized_id": f"doi:{doi}",
        "identifier": doi,
        "doi": doi,
        "url": f"https://doi.org/{doi}",
    }


def parse_github_repo_locator(locator: str) -> Optional[Dict[str, Any]]:
    text = canonicalize_url(locator)
    match = GITHUB_URL_RE.match(text)
    if not match:
        return None
    owner = match.group("owner")
    repo = (match.group("repo") or "").removesuffix(".git")
    rest = match.group("rest") or ""
    source_file = ""
    if rest.startswith("blob/"):
        parts = rest.split("/", 3)
        if len(parts) == 4:
            source_file = parts[3]
    return {
        "provider_type": "github",
        "source_type": "repo",
        "locator_type": "github_repo_url",
        "raw_locator": str(locator or "").strip(),
        "normalized_id": f"github:{owner.lower()}/{repo.lower()}",
        "identifier": f"{owner}/{repo}",
        "repo_full_name": f"{owner}/{repo}",
        "owner": owner,
        "repo": repo,
        "source_file": source_file,
        "url": f"https://github.com/{owner}/{repo}",
    }


def parse_generic_url(locator: str) -> Optional[Dict[str, Any]]:
    text = canonicalize_url(locator)
    if not HTTP_URL_RE.match(text):
        return None
    parsed = urllib.parse.urlsplit(text)
    return {
        "provider_type": "url",
        "source_type": "web",
        "locator_type": "url",
        "raw_locator": str(locator or "").strip(),
        "normalized_id": f"url:{text}",
        "identifier": text,
        "host": parsed.netloc.lower(),
        "url": text,
    }


def detect_locator(locator: str) -> Optional[Dict[str, Any]]:
    for parser in (parse_github_repo_locator, parse_arxiv_locator, parse_doi_locator, parse_generic_url):
        parsed = parser(locator)
        if parsed:
            return parsed
    return None
