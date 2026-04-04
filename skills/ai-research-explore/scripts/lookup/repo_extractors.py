"""Repo-local source extraction for free-first research lookup."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .normalizers import ARXIV_ID_RE, DOI_RE, detect_locator, extract_urls


IGNORED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
}


def _candidate_paths(repo_path: Path) -> List[Path]:
    patterns = [
        "README*",
        "*.md",
        "*.rst",
        "*.yaml",
        "*.yml",
        "*.toml",
        "*.ini",
        "*.py",
    ]
    results: List[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        for path in repo_path.rglob(pattern):
            if not path.is_file():
                continue
            if any(part in IGNORED_DIRS for part in path.relative_to(repo_path).parts):
                continue
            if path.stat().st_size > 256_000:
                continue
            if path in seen:
                continue
            seen.add(path)
            results.append(path)
    return sorted(results)[:120]


def _extract_locators(text: str) -> List[str]:
    found: List[str] = []
    for url in extract_urls(text):
        if url not in found:
            found.append(url)
    for pattern in (ARXIV_ID_RE, DOI_RE):
        for match in pattern.finditer(text):
            raw = match.group(0).strip()
            if raw and raw not in found:
                found.append(raw)
    return found


def _classify_kind(locator: str) -> str:
    parsed = detect_locator(locator)
    if not parsed:
        return "web"
    source_type = parsed.get("source_type")
    if source_type in {"paper", "repo", "web"}:
        return str(source_type)
    return "web"


def extract_repo_local_seeds(repo_path: Path) -> List[Dict[str, Any]]:
    repo_root = Path(repo_path).resolve()
    seeds: List[Dict[str, Any]] = []
    seen_locators: set[str] = set()
    for path in _candidate_paths(repo_root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        locators = _extract_locators(text)
        relative_path = path.relative_to(repo_root).as_posix()
        for locator in locators:
            if locator in seen_locators:
                continue
            seen_locators.add(locator)
            seeds.append(
                {
                    "kind": _classify_kind(locator),
                    "title": locator,
                    "summary": f"Repo-local extracted source from `{relative_path}`.",
                    "query": locator,
                    "source_url": locator if locator.lower().startswith("http") else "",
                    "source_repo": "",
                    "source_file": "",
                    "source_symbol": "",
                    "origin": "repo_local_extracted",
                    "raw_locator": locator,
                    "extracted_from_repo_paths": [relative_path],
                }
            )
    return seeds
