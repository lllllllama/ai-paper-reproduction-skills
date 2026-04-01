#!/usr/bin/env python3
"""Read-only analysis for deep learning research repositories."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List


ENTRYPOINT_PATTERNS = {
    "train": re.compile(r"(train|trainer)", re.IGNORECASE),
    "infer": re.compile(r"(infer|inference|demo|predict)", re.IGNORECASE),
    "eval": re.compile(r"(eval|evaluate|validation|test)", re.IGNORECASE),
    "model": re.compile(r"(model|network|backbone|encoder|decoder)", re.IGNORECASE),
    "config": re.compile(r"(config|configs)", re.IGNORECASE),
}


def collect_candidates(repo: Path) -> Dict[str, List[str]]:
    candidates = {key: [] for key in ENTRYPOINT_PATTERNS}
    for path in repo.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(repo).as_posix()
        if any(part in {"tmp", "artifacts", "repro_outputs", "__pycache__", ".git"} for part in path.parts):
            continue
        for key, pattern in ENTRYPOINT_PATTERNS.items():
            if pattern.search(rel):
                candidates[key].append(rel)
    for key in candidates:
        candidates[key] = sorted(candidates[key])[:20]
    return candidates


def collect_suspicious_patterns(repo: Path) -> List[str]:
    findings: List[str] = []
    python_files = [path for path in repo.rglob("*.py") if "__pycache__" not in path.parts]
    saw_attention = False
    saw_position = False

    for path in python_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(repo).as_posix()
        lower = text.lower()

        if "attention" in lower or "transformer" in lower:
            saw_attention = True
        if any(token in lower for token in ["positional", "position_embedding", "position encoding", "pos_embed"]):
            saw_position = True
        if "sigmoid" in lower and lower.count("sigmoid") >= 2:
            findings.append(f"{rel}: repeated `sigmoid` usage detected; review for duplicated post-processing.")
        if "relu" in lower and "sigmoid" in lower:
            findings.append(f"{rel}: both `relu` and `sigmoid` appear in the same file; check activation order and intent.")
        if ".eval()" in lower and "dropout" in lower:
            findings.append(f"{rel}: review whether dropout-sensitive evaluation behavior is intentional.")
        if "optimizer" in lower and "requires_grad" not in lower and "param_groups" not in lower:
            findings.append(f"{rel}: verify optimizer parameter coverage if custom freezing is expected.")

    if saw_attention and not saw_position:
        findings.append(
            "Repository contains attention-like code but no obvious positional encoding signal was detected; review sequence-order handling."
        )

    unique: List[str] = []
    for item in findings:
        if item not in unique:
            unique.append(item)
    return unique[:20]


def analyze_repo(repo: Path) -> Dict[str, object]:
    readme = repo / "README.md"
    candidates = collect_candidates(repo)
    suspicious = collect_suspicious_patterns(repo)

    summary_lines = [
        f"Target repo: `{repo.resolve()}`",
        f"README present: `{readme.exists()}`",
        f"Top-level items: {', '.join(sorted(item.name for item in repo.iterdir())[:20]) or 'none'}",
        f"Train entry candidates: {', '.join(candidates['train'][:5]) or 'none'}",
        f"Inference entry candidates: {', '.join(candidates['infer'][:5]) or 'none'}",
        f"Evaluation entry candidates: {', '.join(candidates['eval'][:5]) or 'none'}",
    ]

    conservative_suggestions = [
        "Read the main model or backbone file before changing configs.",
        "Verify the train entrypoint and config loading path before inserting new modules.",
        "Treat suspicious patterns as heuristics until confirmed by command-level evidence.",
    ]

    return {
        "repo": str(repo.resolve()),
        "entrypoints": candidates,
        "suspicious_patterns": suspicious,
        "conservative_suggestions": conservative_suggestions,
        "summary_lines": summary_lines,
    }


def write_outputs(output_dir: Path, data: Dict[str, object]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = [
        "# Project Analysis Summary",
        "",
        *[f"- {line}" for line in data["summary_lines"]],
        "",
        "## Conservative Suggestions",
        "",
        *[f"- {line}" for line in data["conservative_suggestions"]],
        "",
    ]
    (output_dir / "SUMMARY.md").write_text("\n".join(summary), encoding="utf-8")

    risks = [
        "# Suspicious Patterns",
        "",
    ]
    patterns = data["suspicious_patterns"]
    if patterns:
        risks.extend(f"- {item}" for item in patterns)
    else:
        risks.append("- No high-signal suspicious patterns were detected by the lightweight heuristic pass.")
    risks.append("")
    (output_dir / "RISKS.md").write_text("\n".join(risks), encoding="utf-8")

    status = {
        "schema_version": "1.0",
        "repo": data["repo"],
        "status": "analyzed",
        "entrypoints": data["entrypoints"],
        "suspicious_patterns": data["suspicious_patterns"],
        "conservative_suggestions": data["conservative_suggestions"],
        "outputs": {
            "summary": "analysis_outputs/SUMMARY.md",
            "risks": "analysis_outputs/RISKS.md",
            "status": "analysis_outputs/status.json",
        },
    }
    (output_dir / "status.json").write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a deep learning research repository conservatively.")
    parser.add_argument("--repo", required=True, help="Path to the target repository.")
    parser.add_argument("--output-dir", default="analysis_outputs", help="Directory for analysis outputs.")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout instead of writing files.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    data = analyze_repo(repo)
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0

    write_outputs(Path(args.output_dir).resolve(), data)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
