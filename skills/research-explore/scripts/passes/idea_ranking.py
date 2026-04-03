"""Idea evaluation and ranking pass for research-explore."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence


POSITIVE_WEIGHTS = {
    "expected_upside": 18.0,
    "single_variable_fit": 14.0,
    "interface_fit": 14.0,
    "rollback_ease": 8.0,
    "innovation_story_strength": 10.0,
    "source_support_strength": 8.0,
    "execution_feasibility": 8.0,
}
NEGATIVE_WEIGHTS = {
    "implementation_risk": 8.0,
    "eval_risk": 6.0,
    "patch_surface": 4.0,
    "dependency_drag": 4.0,
    "execution_cost": 4.0,
    "baseline_distance": 4.0,
}


def clamp(value: Any, default: float = 0.5) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = default
    return max(0.0, min(1.0, numeric))


def hard_gate_failures(card: Dict[str, Any], baseline_gate: Dict[str, Any]) -> List[str]:
    failures: List[str] = []
    if baseline_gate.get("decision") == "abandon":
        failures.append("baseline-gate-abandon")
    if clamp(card.get("single_variable_fit"), default=0.8) < 0.6:
        failures.append("single-variable-fit")
    if clamp(card.get("interface_fit"), default=0.5) < 0.5:
        failures.append("interface-fit")
    if clamp(card.get("patch_surface"), default=0.4) > 0.7:
        failures.append("patch-surface")
    if clamp(card.get("dependency_drag"), default=0.2) > 0.7:
        failures.append("dependency-drag")
    if clamp(card.get("eval_risk"), default=0.5) > 0.6:
        failures.append("eval-risk")
    if str(card.get("short_run_feasibility") or "plausible") == "blocked":
        failures.append("short-run-feasibility")
    return failures


def normalized_score(score_points: float) -> float:
    max_positive = sum(POSITIVE_WEIGHTS.values())
    max_negative = sum(NEGATIVE_WEIGHTS.values())
    return round((score_points + max_negative) / (max_positive + max_negative), 4)


def evaluate_card(card: Dict[str, Any], baseline_gate: Dict[str, Any]) -> Dict[str, Any]:
    contributions: Dict[str, float] = {}
    score_points = 0.0
    execution_feasibility = card.get("execution_feasibility_score", 1.0 - clamp(card.get("execution_cost"), default=0.5))
    for key, weight in POSITIVE_WEIGHTS.items():
        raw_value = execution_feasibility if key == "execution_feasibility" else clamp(card.get(key), default=0.5)
        contribution = round(weight * raw_value, 4)
        contributions[key] = contribution
        score_points += contribution
    for key, weight in NEGATIVE_WEIGHTS.items():
        raw_value = clamp(card.get(key), default=0.5)
        contribution = round(weight * raw_value, 4)
        contributions[key] = -contribution
        score_points -= contribution
    failures = hard_gate_failures(card, baseline_gate)
    evaluated = dict(card)
    evaluated["hard_gate_failures"] = failures
    evaluated["hard_gate_passed"] = not failures
    evaluated["score_breakdown"] = contributions
    evaluated["weighted_total"] = round(score_points, 4)
    evaluated["idea_score"] = normalized_score(score_points)
    return evaluated


def write_evaluation_markdown(
    output_dir: Path,
    ranked_cards: Sequence[Dict[str, Any]],
    baseline_gate: Dict[str, Any],
) -> Path:
    lines = [
        "# Idea Evaluation",
        "",
        f"- Baseline gate: `{baseline_gate.get('decision', 'not-applicable')}`",
        "- Hard gates: baseline_gate != abandon, single_variable_fit >= 0.6, interface_fit >= 0.5, patch_surface <= 0.7, dependency_drag <= 0.7, eval_risk <= 0.6, short_run_feasibility != blocked.",
        "- Soft ranking: expected_upside, single_variable_fit, interface_fit, rollback_ease, innovation_story_strength, source_support_strength, execution_feasibility minus implementation_risk, eval_risk, patch_surface, dependency_drag, execution_cost, baseline_distance.",
        "",
        "## Ranked Cards",
        "",
    ]
    if not ranked_cards:
        lines.append("- None.")
    else:
        for item in ranked_cards:
            lines.append(
                f"- `{item['id']}` score=`{item['idea_score']}` hard_gate=`{item['hard_gate_passed']}` failures={','.join(item['hard_gate_failures']) or 'none'} summary={item['summary']}"
            )
    path = output_dir / "IDEA_EVALUATION.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_idea_ranking_pass(
    *,
    analysis_output_dir: Path,
    cards: Sequence[Dict[str, Any]],
    baseline_gate: Dict[str, Any],
) -> Dict[str, Any]:
    ranked = [evaluate_card(card, baseline_gate) for card in cards]
    ranked.sort(
        key=lambda item: (
            1 if item["hard_gate_passed"] else 0,
            item["idea_score"],
            item.get("expected_upside", 0.0),
            1.0 - item.get("implementation_risk", 1.0),
            item.get("id", ""),
        ),
        reverse=True,
    )
    selected = next((item for item in ranked if item["hard_gate_passed"]), None)
    top_diff = None
    eligible = [item for item in ranked if item["hard_gate_passed"]]
    if len(eligible) >= 2:
        top_diff = round(eligible[0]["idea_score"] - eligible[1]["idea_score"], 4)
    scores_path = analysis_output_dir / "IDEA_SCORES.json"
    scores_path.write_text(json.dumps(ranked, indent=2, ensure_ascii=False), encoding="utf-8")
    markdown_path = write_evaluation_markdown(analysis_output_dir, ranked, baseline_gate)
    return {
        "schema_version": "1.0",
        "artifact_paths": [str(markdown_path), str(scores_path)],
        "ranked_ideas": ranked,
        "selected_idea": selected,
        "decision": "selected" if selected else "not-configured",
        "top_idea_score_diff": top_diff,
    }
