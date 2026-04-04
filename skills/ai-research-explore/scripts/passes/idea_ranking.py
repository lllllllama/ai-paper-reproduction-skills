"""Idea evaluation and ranking pass for ai-research-explore."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple


POSITIVE_WEIGHTS = {
    "expected_upside": 14.0,
    "single_variable_fit": 10.0,
    "groundedness": 10.0,
    "source_support_strength": 9.0,
    "interface_fit": 9.0,
    "rollback_ease": 6.0,
    "novelty_estimate": 5.0,
    "ablation_clarity": 8.0,
    "implementation_story_clarity": 8.0,
    "execution_feasibility": 7.0,
}
NEGATIVE_WEIGHTS = {
    "implementation_risk": 8.0,
    "eval_risk": 7.0,
    "patch_surface": 5.0,
    "dependency_drag": 5.0,
    "execution_cost": 4.0,
    "baseline_distance": 3.0,
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


def score_payload(value: float, weight: float, direction: str) -> Dict[str, Any]:
    signed = round(weight * value, 4)
    contribution = signed if direction == "positive" else -signed
    return {
        "value": round(value, 4),
        "weight": weight,
        "direction": direction,
        "contribution": round(contribution, 4),
    }


def evaluate_card(card: Dict[str, Any], baseline_gate: Dict[str, Any]) -> Dict[str, Any]:
    raw_scores: Dict[str, float] = {}
    breakdown: Dict[str, Dict[str, Any]] = {}
    score_points = 0.0
    execution_feasibility = card.get("execution_feasibility_score", 1.0 - clamp(card.get("execution_cost"), default=0.5))
    for key, weight in POSITIVE_WEIGHTS.items():
        raw_value = execution_feasibility if key == "execution_feasibility" else clamp(card.get(key), default=0.5)
        raw_scores[key] = round(raw_value, 4)
        item = score_payload(raw_value, weight, "positive")
        breakdown[key] = item
        score_points += item["contribution"]
    for key, weight in NEGATIVE_WEIGHTS.items():
        raw_value = clamp(card.get(key), default=0.5)
        raw_scores[key] = round(raw_value, 4)
        item = score_payload(raw_value, weight, "negative")
        breakdown[key] = item
        score_points += item["contribution"]
    failures = hard_gate_failures(card, baseline_gate)
    evaluated = dict(card)
    evaluated["hard_gate_failures"] = failures
    evaluated["hard_gate_passed"] = not failures
    evaluated["score_inputs"] = raw_scores
    evaluated["score_breakdown"] = breakdown
    evaluated["weighted_total"] = round(score_points, 4)
    evaluated["idea_score"] = normalized_score(score_points)
    evaluated["seed_origin"] = str(card.get("seed_origin") or "researcher")
    return evaluated


def selection_pool(eligible: Sequence[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]], str]:
    researcher_eligible = [
        item
        for item in eligible
        if str(item.get("seed_origin") or "researcher") == "researcher"
    ]
    if researcher_eligible:
        return (
            "researcher",
            researcher_eligible,
            "researcher hard precedence kept final selection inside the researcher-provided pool.",
        )
    return (
        "all-eligible",
        list(eligible),
        "No researcher idea passed hard gates, so the full eligible pool remained available.",
    )


def ranking_sort_key(item: Dict[str, Any]) -> Tuple[int, float, float, float, float, str]:
    return (
        1 if item["hard_gate_passed"] else 0,
        item["idea_score"],
        item.get("expected_upside", 0.0),
        item.get("groundedness", 0.0),
        1.0 - item.get("implementation_risk", 1.0),
        item.get("id", ""),
    )


def pool_priority(item: Dict[str, Any], active_pool: str) -> int:
    if active_pool == "researcher":
        return 1 if str(item.get("seed_origin") or "researcher") == "researcher" else 0
    return 1 if item.get("hard_gate_passed") else 0


def write_evaluation_markdown(
    output_dir: Path,
    ranked_cards: Sequence[Dict[str, Any]],
    baseline_gate: Dict[str, Any],
    *,
    selected_idea: Dict[str, Any] | None,
    active_selection_pool: str,
    selection_reason: str,
) -> Path:
    lines = [
        "# Idea Evaluation",
        "",
        f"- Baseline gate: `{baseline_gate.get('decision', 'not-applicable')}`",
        "- Hard gates: baseline_gate != abandon, single_variable_fit >= 0.6, interface_fit >= 0.5, patch_surface <= 0.7, dependency_drag <= 0.7, eval_risk <= 0.6, short_run_feasibility != blocked.",
        "- Soft scoring uses explicit breakdown fields rather than a black-box total.",
        f"- Active selection pool: `{active_selection_pool}`",
        f"- Selection reason: {selection_reason}",
        "",
        "## Ranked Cards",
        "",
    ]
    if not ranked_cards:
        lines.append("- None.")
    else:
        for item in ranked_cards:
            lines.append(
                f"- `{item['id']}` origin=`{item.get('seed_origin', 'researcher')}` score=`{item['idea_score']}` hard_gate=`{item['hard_gate_passed']}` failures={','.join(item['hard_gate_failures']) or 'none'} summary={item['summary']}"
            )
    lines.extend(["", "## Selected Idea", ""])
    if selected_idea is None:
        lines.append("- None.")
    else:
        lines.append(
            f"- `{selected_idea['id']}` origin=`{selected_idea.get('seed_origin', 'researcher')}` score=`{selected_idea['idea_score']}`"
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
    eligible = [item for item in ranked if item["hard_gate_passed"]]
    active_selection_pool, active_candidates, selection_reason = selection_pool(eligible)
    active_candidates.sort(key=ranking_sort_key, reverse=True)
    selected = active_candidates[0] if active_candidates else None
    top_diff = None
    if len(active_candidates) >= 2:
        top_diff = round(active_candidates[0]["idea_score"] - active_candidates[1]["idea_score"], 4)
    ranked.sort(
        key=lambda item: (
            pool_priority(item, active_selection_pool),
            *ranking_sort_key(item),
        ),
        reverse=True,
    )
    if selected is not None:
        selected = dict(selected)
        selected["selection_pool"] = active_selection_pool
        selected["selection_reason"] = selection_reason
        selected["selected_via_hard_precedence"] = active_selection_pool == "researcher"
    scores_path = analysis_output_dir / "IDEA_SCORES.json"
    scores_path.write_text(json.dumps(ranked, indent=2, ensure_ascii=False), encoding="utf-8")
    markdown_path = write_evaluation_markdown(
        analysis_output_dir,
        ranked,
        baseline_gate,
        selected_idea=selected,
        active_selection_pool=active_selection_pool,
        selection_reason=selection_reason,
    )
    return {
        "schema_version": "1.0",
        "artifact_paths": [str(markdown_path), str(scores_path)],
        "ranked_ideas": ranked,
        "selected_idea": selected,
        "decision": "selected" if selected else "not-configured",
        "top_idea_score_diff": top_diff,
        "active_selection_pool": active_selection_pool,
        "selection_reason": selection_reason,
        "selected_idea_breakdown": selected.get("score_breakdown") if selected else {},
    }

