#!/usr/bin/env python3
"""Generate a small exploratory variant matrix for isolated runs."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Any, Dict, List


def load_spec(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def current_research_value(spec: Dict[str, Any]) -> str:
    return str(spec.get("current_research") or spec.get("baseline_ref") or "unknown")


def build_variants(spec: Dict[str, Any]) -> Dict[str, Any]:
    axes = spec.get("variant_axes", {})
    keys = sorted(axes)
    values = [axes[key] for key in keys]
    subset_sizes = spec.get("subset_sizes", [None])
    short_run_steps = spec.get("short_run_steps", [None])
    current_research = current_research_value(spec)

    variants: List[Dict[str, Any]] = []
    index = 1
    for combo in itertools.product(*values):
        axis_values = dict(zip(keys, combo))
        for subset_size in subset_sizes:
            for step_limit in short_run_steps:
                variant_id = f"variant-{index:03d}"
                variants.append(
                    {
                        "id": variant_id,
                        "axes": axis_values,
                        "subset_size": subset_size,
                        "short_run_steps": step_limit,
                        "current_research": current_research,
                        "baseline_ref": spec.get("baseline_ref", current_research),
                        "base_command": spec.get("base_command"),
                    }
                )
                index += 1

    return {
        "schema_version": "1.0",
        "current_research": current_research,
        "baseline_ref": spec.get("baseline_ref", current_research),
        "base_command": spec.get("base_command"),
        "variant_count": len(variants),
        "variants": variants,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an exploratory variant matrix.")
    parser.add_argument("--spec-json", required=True, help="Path to the exploration spec JSON file.")
    parser.add_argument("--output-json", help="Optional output path for the generated matrix.")
    parser.add_argument("--json", action="store_true", help="Emit the matrix to stdout.")
    args = parser.parse_args()

    payload = build_variants(load_spec(Path(args.spec_json).resolve()))
    if args.output_json:
        Path(args.output_json).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.json or not args.output_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
