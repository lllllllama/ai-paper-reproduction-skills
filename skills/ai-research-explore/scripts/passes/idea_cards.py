"""Hypothesis-card pass for ai-research-explore."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence


REQUIRED_FIELDS = [
    "id",
    "summary",
    "rationale",
    "target_component",
    "source_reference",
    "expected_upside",
    "single_variable_fit",
    "implementation_risk",
    "eval_risk",
    "rollback_ease",
    "patch_surface",
    "dependency_drag",
    "validation_path",
    "innovation_note",
]

ALLOWED_PATCH_CLASSES = {
    "config-only",
    "import-glue",
    "module-transplant-shim",
}


def build_cards(improvement_items: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cards: List[Dict[str, Any]] = []
    for item in improvement_items:
        card = dict(item)
        missing = [field for field in REQUIRED_FIELDS if field not in card]
        if missing:
            raise ValueError(f"Improvement item `{item.get('id', 'unknown')}` is missing required card fields: {missing}")
        patch_class = str(card.get("patch_class") or "").strip().lower()
        card["patch_class"] = patch_class if patch_class in ALLOWED_PATCH_CLASSES else "config-only"
        card["patch_class_source"] = "campaign" if patch_class in ALLOWED_PATCH_CLASSES else "default"
        card.setdefault("short_run_feasibility", "plausible")
        cards.append(card)
    return cards


def run_idea_card_pass(*, analysis_output_dir: Path, improvement_items: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    cards = build_cards(improvement_items)
    path = analysis_output_dir / "IDEA_CARDS.json"
    path.write_text(json.dumps(cards, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "schema_version": "1.0",
        "artifact_path": str(path),
        "cards": cards,
    }

