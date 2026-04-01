#!/usr/bin/env python3
"""Run lightweight trigger boundary checks for the local skill set.

This script is not intended to emulate Codex's exact routing behavior. It is a
small, auditable lexical router that helps catch obvious scope overlap between
skills. When a prompt triggers multiple skills here, it usually means the
descriptions or guardrails need tightening.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9._/-]*", re.IGNORECASE)
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "before",
    "by",
    "do",
    "for",
    "from",
    "if",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "only",
    "or",
    "that",
    "the",
    "this",
    "to",
    "use",
    "user",
    "when",
    "with",
    "without",
    "not",
    "main",
    "skill",
    "sub",
    "ai",
}
HIGH_SIGNAL_TOKENS = {
    "readme",
    "documented",
    "inference",
    "evaluation",
    "training",
    "conda",
    "checkpoint",
    "dataset",
    "cache",
    "smoke",
    "audit",
    "traceback",
    "cuda",
    "oom",
    "nan",
    "debug",
    "entrypoints",
    "insertion",
    "structure",
}
SKILL_NAME_BOOST = 100.0


@dataclass
class SkillInfo:
    name: str
    description: str


def parse_front_matter(skill_md: Path) -> Dict[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{skill_md} is missing YAML front matter.")
    _, front_matter, _ = text.split("---", 2)
    data: Dict[str, str] = {}
    for raw_line in front_matter.splitlines():
        line = raw_line.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def normalize_tokens(text: str) -> List[str]:
    raw = [token.lower() for token in TOKEN_RE.findall(text)]
    return [token for token in raw if token not in STOPWORDS and len(token) > 2]


def contains_any(text: str, phrases: Iterable[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def repo_context(text: str) -> bool:
    return contains_any(
        text,
        [
            "repo",
            "repository",
            "readme",
            "codebase",
            "model",
            "backbone",
            "config",
            "train.py",
            "infer.py",
            "eval.py",
        ],
    )


def setup_intent(text: str) -> bool:
    return contains_any(
        text,
        [
            "conda",
            "environment",
            "env ",
            "checkpoint",
            "dataset",
            "cache",
            "setup",
            "prepare",
            "asset plan",
            "before any run",
            "before we execute",
        ],
    )


def setup_anchor(text: str) -> bool:
    return contains_any(
        text,
        [
            "conda",
            "environment",
            "env ",
            "setup",
            "prepare",
            "asset plan",
            "before any run",
            "before we execute",
            "checkpoint path",
            "cache path",
        ],
    )


def scan_intent(text: str) -> bool:
    return contains_any(
        text,
        [
            "scan",
            "read the readme",
            "extract documented",
            "classify",
            "tell me the documented",
            "do not run",
            "don't run",
            "without running",
        ],
    )


def verify_intent(text: str) -> bool:
    return contains_any(
        text,
        [
            "run the selected documented",
            "selected documented",
            "run inference",
            "run evaluation",
            "smoke",
            "sanity",
            "execute",
            "write summary.md",
            "write commands.md",
            "write log.md",
            "write status.json",
            "standardized outputs",
            "capture evidence",
        ],
    )


def training_intent(text: str) -> bool:
    return contains_any(
        text,
        [
            "run the selected training command",
            "run the documented training command",
            "training command",
            "kick off training",
            "full training kickoff",
            "startup verification",
            "short-run verification",
            "resume training",
            "resume from checkpoint",
            "monitor training status",
            "train_outputs",
        ],
    )


def explore_authorization(text: str) -> bool:
    return contains_any(
        text,
        [
            "explore",
            "try it",
            "scan a batch",
            "idle gpu",
            "experiment branch",
            "isolated branch",
            "isolated worktree",
            "candidate only",
            "not the trusted baseline",
            "okay to commit exploratory modifications",
        ],
    )


def explore_code_intent(text: str) -> bool:
    return contains_any(
        text,
        [
            "lora",
            "adapter",
            "transplant module",
            "copy the module",
            "copy a module",
            "replace the head",
            "backbone adaptation",
            "migrate module",
            "module combination",
            "stitch together",
            "smallest adaptation",
        ],
    )


def explore_run_intent(text: str) -> bool:
    return contains_any(
        text,
        [
            "small subset",
            "short-cycle",
            "short cycle",
            "batch sweep",
            "sweep",
            "idle gpu",
            "top runs",
            "guess-and-check",
            "quick transfer-learning",
            "rank candidate runs",
            "exploratory runs",
        ],
    )


def paper_gap_intent(text: str) -> bool:
    return contains_any(
        text,
        [
            "linked paper",
            "arxiv",
            "openreview",
            "split",
            "protocol",
            "dataset version",
            "preprocessing",
            "readme is missing",
            "readme is ambiguous",
            "reproduction-critical detail",
            "checkpoint mapping",
        ],
    )


def paper_summary_intent(text: str) -> bool:
    if contains_any(text, ["do not summarize", "don't summarize", "not summarize"]):
        return False
    return contains_any(text, ["summarize", "novelty", "related work", "overview"])


def analysis_intent(text: str) -> bool:
    return contains_any(
        text,
        [
            "understand this repository",
            "read and understand",
            "analyze the project",
            "analyze this repo",
            "inspect model structure",
            "model structure",
            "training entrypoint",
            "inference entrypoint",
            "config relationship",
            "insertion point",
            "suspicious pattern",
            "read-only analysis",
            "walk me through the project",
            "review the code structure",
        ],
    )


def error_signal(text: str) -> bool:
    if contains_any(text, ["no active traceback", "no traceback", "without an active failure"]):
        return False
    return contains_any(
        text,
        [
            "traceback",
            "runtimeerror",
            "valueerror",
            "cuda out of memory",
            "oom",
            "nccl",
            "checkpoint load",
            "missing key",
            "unexpected key",
            "size mismatch",
            "shape mismatch",
            "expected all tensors to be on the same device",
            "loss is nan",
            "nan",
            "not converging",
            "training failed",
            "segmentation fault",
            "filenotfounderror",
            "module not found",
        ],
    )


def debug_intent(text: str) -> bool:
    return contains_any(
        text,
        [
            "debug",
            "why is this failing",
            "root cause",
            "diagnose",
            "patch plan",
            "terminal error",
            "training failure",
            "inference failure",
        ],
    )


def research_debug_context(text: str) -> bool:
    return contains_any(
        text,
        [
            "cuda",
            "checkpoint",
            "tensor",
            "loss",
            "inference",
            "evaluation",
            "distributed",
            "ddp",
            "nccl",
            "model",
            "backbone",
            "repo",
            "repository",
            "train.py",
            "infer.py",
            "eval.py",
        ],
    )


def score_prompt(prompt: str, skill: SkillInfo) -> float:
    prompt_tokens = normalize_tokens(prompt)
    description_tokens = normalize_tokens(skill.description)
    if not prompt_tokens or not description_tokens:
        return 0.0

    prompt_text = prompt.lower()
    if skill.name in prompt_text:
        return SKILL_NAME_BOOST

    desc_set = set(description_tokens)
    overlap = 0.0
    for token in prompt_tokens:
        if token in desc_set:
            overlap += 2.0 if token in HIGH_SIGNAL_TOKENS else 1.0

    bigrams = set(zip(prompt_tokens, prompt_tokens[1:]))
    skill_bigrams = set(zip(description_tokens, description_tokens[1:]))
    overlap += 1.5 * len(bigrams & skill_bigrams)

    return max(apply_skill_gates(skill.name, prompt_text, overlap), 0.0)


def apply_skill_gates(skill_name: str, prompt_text: str, base_score: float) -> float:
    if base_score <= 0:
        return 0.0

    has_repo = repo_context(prompt_text)
    wants_scan = scan_intent(prompt_text)
    wants_setup = setup_intent(prompt_text)
    has_setup_anchor = setup_anchor(prompt_text)
    wants_verify = verify_intent(prompt_text)
    wants_train = training_intent(prompt_text)
    has_explore_auth = explore_authorization(prompt_text)
    wants_explore_code = explore_code_intent(prompt_text)
    wants_explore_run = explore_run_intent(prompt_text)
    wants_paper_gap = paper_gap_intent(prompt_text)
    wants_summary = paper_summary_intent(prompt_text)
    wants_analysis = analysis_intent(prompt_text)
    has_error = error_signal(prompt_text)
    wants_debug = debug_intent(prompt_text)
    has_research_debug_context = research_debug_context(prompt_text)
    forbids_run = contains_any(prompt_text, ["do not run", "don't run", "without running", "before we execute"])

    if skill_name == "ai-paper-reproduction":
        if not has_repo:
            return 0.0
        explicit_repro = contains_any(prompt_text, ["reproduce", "reproduction", "end-to-end", "orchestrate", "repro_outputs"])
        if explicit_repro:
            base_score += 6.0
        if wants_summary:
            return 0.0
        if wants_analysis or has_error or wants_debug:
            return 0.0
        if wants_scan and not explicit_repro:
            return 0.0
        if wants_setup and not wants_verify and not wants_train and not explicit_repro:
            return 0.0
        if wants_paper_gap and not explicit_repro:
            return 0.0
        if wants_train and not explicit_repro:
            return 0.0
        if has_explore_auth:
            return 0.0
        return base_score

    if skill_name == "repo-intake-and-plan":
        if not (has_repo and wants_scan):
            return 0.0
        if wants_verify and not forbids_run:
            base_score -= 4.0
        if wants_train:
            base_score -= 4.0
        if has_explore_auth:
            base_score -= 4.0
        if wants_setup and not wants_scan:
            base_score -= 3.0
        return base_score + 2.0

    if skill_name == "env-and-assets-bootstrap":
        if not has_repo or not wants_setup or not has_setup_anchor:
            return 0.0
        if wants_verify or wants_train:
            base_score -= 2.0
        if has_explore_auth:
            base_score -= 4.0
        if has_error or wants_debug:
            base_score -= 3.0
        return base_score + 3.0

    if skill_name == "minimal-run-and-audit":
        if forbids_run:
            return 0.0
        if wants_train:
            return 0.0
        if not wants_verify:
            return 0.0
        if has_explore_auth:
            return 0.0
        if wants_scan or wants_setup or has_error or wants_debug:
            base_score -= 2.0
        return base_score + 3.0

    if skill_name == "run-train":
        if has_error or wants_debug:
            return 0.0
        if not wants_train:
            return 0.0
        if has_explore_auth:
            return 0.0
        if not (has_repo or contains_any(prompt_text, ["selected training command", "documented training command", "resume from checkpoint"])):
            return 0.0
        if wants_verify and not wants_train:
            base_score -= 2.0
        return base_score + 4.0

    if skill_name == "explore-code":
        if has_error or wants_debug:
            return 0.0
        if not (has_explore_auth and wants_explore_code):
            return 0.0
        if wants_train and not wants_explore_code:
            base_score -= 2.0
        return base_score + 5.0

    if skill_name == "explore-run":
        if has_error or wants_debug:
            return 0.0
        if not (has_explore_auth and wants_explore_run):
            return 0.0
        return base_score + 5.0

    if skill_name == "paper-context-resolver":
        if wants_summary:
            return 0.0
        if not wants_paper_gap:
            return 0.0 if base_score < 4 else base_score - 4.0
        if wants_setup and not wants_paper_gap:
            base_score -= 4.0
        return base_score + 4.0

    if skill_name == "analyze-project":
        if has_error or wants_debug:
            base_score -= 5.0
        if not (has_repo and wants_analysis):
            return 0.0
        if wants_verify or wants_setup or wants_train or has_explore_auth:
            base_score -= 2.0
        return base_score + 4.0

    if skill_name == "safe-debug":
        if not (has_error or wants_debug):
            return 0.0
        if has_explore_auth:
            return 0.0
        if wants_debug and not has_error and not has_research_debug_context:
            return 0.0
        if wants_analysis and not has_error:
            base_score -= 4.0
        if wants_setup and not has_error:
            base_score -= 3.0
        return base_score + 5.0

    return base_score


def explicitly_named_skills(prompt: str, skills: Iterable[SkillInfo]) -> List[str]:
    prompt_text = prompt.lower()
    return [skill.name for skill in skills if skill.name in prompt_text]


def load_skills(repo_root: Path) -> List[SkillInfo]:
    skills: List[SkillInfo] = []
    skills_root = repo_root / "skills"
    for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        fm = parse_front_matter(skill_md)
        skills.append(SkillInfo(name=fm["name"], description=fm["description"]))
    return skills


def rank_skills(prompt: str, skills: Iterable[SkillInfo]) -> List[Tuple[str, float]]:
    ranked = [(skill.name, score_prompt(prompt, skill)) for skill in skills]
    ranked.sort(key=lambda item: (-item[1], item[0]))
    return ranked


def evaluate_case(case: Dict[str, object], skills: List[SkillInfo], threshold: float) -> Dict[str, object]:
    prompt = str(case["prompt"])
    ranked = rank_skills(prompt, skills)
    named = explicitly_named_skills(prompt, skills)
    triggered = [name for name, score in ranked if score >= threshold]
    if named:
        triggered = [name for name in triggered if name in named]

    expected_any = list(case.get("expected_any", []))
    forbidden = set(case.get("forbidden", []))
    expected_top = case.get("expected_top")

    failures: List[str] = []
    if expected_any:
        if not any(name in triggered for name in expected_any):
            failures.append(f"Expected one of {expected_any}, got {triggered or 'none'}")
    else:
        if triggered:
            failures.append(f"Expected no trigger, got {triggered}")

    if expected_top is not None:
        top_name = ranked[0][0] if ranked else None
        if top_name != expected_top:
            failures.append(f"Expected top skill `{expected_top}`, got `{top_name}`")

    forbidden_hits = [name for name in triggered if name in forbidden]
    if forbidden_hits:
        failures.append(f"Forbidden skills triggered: {forbidden_hits}")

    return {
        "id": case["id"],
        "type": case["type"],
        "ok": not failures,
        "triggered": triggered,
        "ranked": ranked,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run boundary and negative trigger tests for skills.")
    parser.add_argument(
        "--cases",
        default="tests/trigger_cases.json",
        help="Path to the trigger case JSON file.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=3.0,
        help="Score threshold required to count as triggered.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    skills = load_skills(repo_root)
    case_payload = json.loads((repo_root / args.cases).read_text(encoding="utf-8"))
    results = [evaluate_case(case, skills, args.threshold) for case in case_payload["cases"]]
    failures = [item for item in results if not item["ok"]]

    payload = {
        "ok": not failures,
        "threshold": args.threshold,
        "skill_count": len(skills),
        "case_count": len(results),
        "failures": failures,
        "results": results,
    }

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"ok: {payload['ok']}")
        print(f"cases: {payload['case_count']}")
        print(f"failures: {len(failures)}")
        for result in results:
            status = "PASS" if result["ok"] else "FAIL"
            print(f"{status}: {result['id']} -> {result['triggered']}")
            if not result["ok"]:
                for failure in result["failures"]:
                    print(f"  - {failure}")

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
