"""Human-readable lookup inventory writers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Sequence


def write_sources_summary(sources_dir: Path, records: Sequence[Dict[str, Any]]) -> Path:
    lines = [
        "# Sources Summary",
        "",
        "Research lookup for `ai-research-explore` is free-first, cache-first, and auditable.",
        "",
        "## Cached Records",
        "",
    ]
    if not records:
        lines.append("- None.")
    else:
        for item in records:
            triple = " / ".join(
                part
                for part in [
                    str(item.get("source_repo") or ""),
                    str(item.get("source_file") or ""),
                    str(item.get("source_symbol") or ""),
                ]
                if part
            ) or "no-source-triple"
            lines.append(
                f"- `{item.get('source_id')}` `{item.get('provider_type')}` `{item.get('title')}` -> `{item.get('artifact_path')}` evidence={item.get('evidence_class', 'unknown')} triple={triple}"
            )
    summary_path = sources_dir / "SUMMARY.md"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    return summary_path


def write_source_inventory(
    analysis_output_dir: Path,
    *,
    records: Sequence[Dict[str, Any]],
    repo_local_extractions: Sequence[Dict[str, Any]],
    cache_stats: Dict[str, Any],
) -> Path:
    by_class: Dict[str, int] = {}
    for item in records:
        key = str(item.get("evidence_class") or "unknown")
        by_class[key] = by_class.get(key, 0) + 1
    lines = [
        "# Source Inventory",
        "",
        "Human-readable inventory for free-first, provider-optional research lookup.",
        "",
        "## Evidence Breakdown",
        "",
    ]
    if by_class:
        for key in sorted(by_class):
            lines.append(f"- `{key}`: {by_class[key]}")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Cache Stats",
            "",
            f"- Cache hits: {cache_stats.get('cache_hits', 0)}",
            f"- Cache misses: {cache_stats.get('cache_misses', 0)}",
            f"- Merge upgrades: {cache_stats.get('merge_upgrades', 0)}",
            "",
            "## Repo-local Extractions",
            "",
        ]
    )
    if repo_local_extractions:
        for item in repo_local_extractions[:20]:
            paths = ", ".join(item.get("extracted_from_repo_paths", [])) or "unknown-path"
            lines.append(f"- `{item.get('raw_locator') or item.get('query')}` from `{paths}`")
    else:
        lines.append("- None.")
    lines.extend(["", "## Resolved Records", ""])
    if records:
        for item in records:
            lines.append(
                f"- `{item.get('source_id')}` `{item.get('source_type')}` `{item.get('provider_type')}` `{item.get('title')}` evidence=`{item.get('evidence_class')}`"
            )
    else:
        lines.append("- None.")
    path = analysis_output_dir / "SOURCE_INVENTORY.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

