#!/usr/bin/env python3
"""Shared writer for exploratory code and exploratory run bundles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def load_context(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def bullets(items: Iterable[str]) -> str:
    values = [item for item in items if item]
    if not values:
        return "- None."
    return "\n".join(f"- {item}" for item in values)


def format_source_refs(source_repo_refs: Iterable[Dict[str, Any]]) -> List[str]:
    refs = []
    for item in source_repo_refs:
        repo = item.get("repo", "unknown")
        ref = item.get("ref", "unknown")
        note = item.get("note")
        line = f"- `{repo}` @ `{ref}`"
        if note:
            line += f": {note}"
        refs.append(line)
    return refs or ["- None."]


def write_changeset(output_dir: Path, context: Dict[str, Any], mode: str) -> None:
    title = "# Explore Changeset"
    intent_title = "## Exploratory code focus" if mode == "code" else "## Experiment focus"
    lines = [
        title,
        "",
        f"- Mode: `{mode}`",
        f"- Baseline ref: `{context.get('baseline_ref', 'unknown')}`",
        f"- Experiment branch: `{context.get('experiment_branch', 'unknown')}`",
        f"- Isolated workspace: `{context.get('isolated_workspace', True)}`",
        f"- Trusted promotion candidate: `{context.get('trusted_promote_candidate', False)}`",
        "",
        "## Source references",
        "",
        *format_source_refs(context.get("source_repo_refs", [])),
        "",
        intent_title,
        "",
        bullets(context.get("changes_summary", [])),
        "",
        "## Notes",
        "",
        bullets(context.get("notes", [])),
        "",
    ]
    (output_dir / "CHANGESET.md").write_text("\n".join(lines), encoding="utf-8")


def write_top_runs(output_dir: Path, context: Dict[str, Any], mode: str) -> None:
    lines = [
        "# Top Runs",
        "",
        f"- Variant count: `{context.get('variant_count', 0)}`",
        "",
        "## Best runs",
        "",
    ]
    best_runs = context.get("best_runs", [])
    if not best_runs:
        lines.append("- None.")
    else:
        for item in best_runs:
            lines.append(
                f"- `{item.get('id', 'unknown')}` metric=`{item.get('metric', 'unknown')}` summary={item.get('summary', 'none')}"
            )
    lines.extend(
        [
            "",
            "## Recommended next trials",
            "",
            bullets(context.get("recommended_next_trials", [])),
            "",
        ]
    )
    if mode == "run":
        lines.extend(
            [
                "## Execution notes",
                "",
                bullets(context.get("execution_notes", [])),
                "",
            ]
        )
    (output_dir / "TOP_RUNS.md").write_text("\n".join(lines), encoding="utf-8")


def write_status(output_dir: Path, context: Dict[str, Any], mode: str) -> None:
    payload = {
        "schema_version": context.get("schema_version", "1.0"),
        "mode": mode,
        "status": context.get("status", "planned"),
        "baseline_ref": context.get("baseline_ref"),
        "experiment_branch": context.get("experiment_branch"),
        "isolated_workspace": context.get("isolated_workspace", True),
        "source_repo_refs": context.get("source_repo_refs", []),
        "variant_count": context.get("variant_count", 0),
        "best_runs": context.get("best_runs", []),
        "recommended_next_trials": context.get("recommended_next_trials", []),
        "trusted_promote_candidate": context.get("trusted_promote_candidate", False),
        "explicit_explore_authorization": context.get("explicit_explore_authorization", True),
        "outputs": {
            "changeset": "explore_outputs/CHANGESET.md",
            "top_runs": "explore_outputs/TOP_RUNS.md",
            "status": "explore_outputs/status.json",
        },
        "notes": context.get("notes", []),
    }
    (output_dir / "status.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_bundle(mode: str, output_dir: Path, context: Dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_changeset(output_dir, context, mode)
    write_top_runs(output_dir, context, mode)
    write_status(output_dir, context, mode)


def main(default_mode: str = "code", default_output_dir: Optional[str] = None) -> int:
    parser = argparse.ArgumentParser(description="Write exploratory output bundles.")
    parser.add_argument("--context-json", required=True, help="Path to a context JSON file.")
    parser.add_argument("--mode", choices=["code", "run"], default=default_mode)
    parser.add_argument(
        "--output-dir",
        default=default_output_dir or "explore_outputs",
        help="Directory where output files will be written.",
    )
    args = parser.parse_args()

    context = load_context(Path(args.context_json).resolve())
    write_bundle(args.mode, Path(args.output_dir).resolve(), context)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
