#!/usr/bin/env python3
"""Lightweight schema checks for ai-research-explore analysis artifacts."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


def write_repo(root: Path) -> None:
    (root / "README.md").write_text(
        "# Demo Contract Repo\n\n"
        "## Training\n\n"
        "```bash\n"
        "python train.py --config configs/demo.yaml\n"
        "```\n",
        encoding="utf-8",
    )
    (root / "train.py").write_text("print('train stub')\n", encoding="utf-8")
    (root / "model.py").write_text("class DemoModel:\n    pass\n", encoding="utf-8")
    (root / "configs").mkdir()
    (root / "configs" / "demo.yaml").write_text("model: demo\n", encoding="utf-8")


def init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "codex@example.com"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Codex"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=root, check=True, capture_output=True, text=True)


def remove_readonly(func, path, _excinfo) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


def require_keys(payload: dict, keys: set[str], label: str) -> None:
    missing = sorted(key for key in keys if key not in payload)
    if missing:
        raise AssertionError(f"{label} is missing keys: {missing}")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    orchestrator = repo_root / "skills" / "ai-research-explore" / "scripts" / "orchestrate_explore.py"

    temp_root = Path(tempfile.mkdtemp(prefix="codex-research-explore-contracts-", dir=repo_root))
    try:
        sample_repo = temp_root / "sample_repo"
        sample_repo.mkdir()
        write_repo(sample_repo)
        init_git_repo(sample_repo)

        spec = {
            "current_research": "contract-branch@abc1234",
            "base_command": "python train.py --config configs/demo.yaml",
            "variant_axes": {"adapter": ["none", "lora"]},
            "subset_sizes": [16],
            "short_run_steps": [5],
        }
        spec_path = temp_root / "variant-spec.json"
        spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")

        output_dir = temp_root / "explore_outputs"
        subprocess.run(
            [
                sys.executable,
                str(orchestrator),
                "--repo",
                str(sample_repo),
                "--current-research",
                "contract-branch@abc1234",
                "--output-dir",
                str(output_dir),
                "--variant-spec-json",
                str(spec_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        analysis_dir = temp_root / "analysis_outputs"
        idea_seeds = json.loads((analysis_dir / "IDEA_SEEDS.json").read_text(encoding="utf-8"))
        atomic_map = json.loads((analysis_dir / "ATOMIC_IDEA_MAP.json").read_text(encoding="utf-8"))
        fidelity = json.loads((analysis_dir / "IMPLEMENTATION_FIDELITY.json").read_text(encoding="utf-8"))
        status = json.loads((analysis_dir / "status.json").read_text(encoding="utf-8"))
        scores = json.loads((analysis_dir / "IDEA_SCORES.json").read_text(encoding="utf-8"))
        evaluation_md = (analysis_dir / "IDEA_EVALUATION.md").read_text(encoding="utf-8")

        if not idea_seeds["generated_ideas"]:
            raise AssertionError("contract test expected synthesized idea seeds")
        require_keys(
            idea_seeds["generated_ideas"][0],
            {
                "id",
                "summary",
                "seed_origin",
                "context_anchor",
                "task_family_binding",
                "dataset_binding",
                "evaluation_binding",
                "constraint_notes",
            },
            "IDEA_SEEDS.json generated idea",
        )
        if not atomic_map["atomic_units"]:
            raise AssertionError("contract test expected atomic units")
        require_keys(
            atomic_map["atomic_units"][0],
            {
                "atomic_id",
                "concept_name",
                "formula_support",
                "code_support",
                "target_file_candidates",
                "validation_strategy",
                "scientific_meaning_risk",
            },
            "ATOMIC_IDEA_MAP.json atomic unit",
        )
        if not fidelity["fidelity_units"]:
            raise AssertionError("contract test expected fidelity units")
        require_keys(
            fidelity["fidelity_units"][0],
            {
                "planned_implementation_sites",
                "heuristic_implementation_sites",
                "observed_implementation_sites",
                "evidence_provenance",
                "verification_level",
                "fidelity_state",
            },
            "IMPLEMENTATION_FIDELITY.json fidelity unit",
        )
        if set(fidelity["fidelity_units"][0]["planned_implementation_sites"]) & set(fidelity["fidelity_units"][0]["observed_implementation_sites"]):
            raise AssertionError("planned implementation sites leaked into observed implementation sites")
        if status["outputs"]["idea_seeds"] != "analysis_outputs/IDEA_SEEDS.json":
            raise AssertionError("analysis status lost idea_seeds output path")
        if status["outputs"]["atomic_idea_map"] != "analysis_outputs/ATOMIC_IDEA_MAP.json":
            raise AssertionError("analysis status lost atomic_idea_map output path")
        if status["outputs"]["implementation_fidelity"] != "analysis_outputs/IMPLEMENTATION_FIDELITY.json":
            raise AssertionError("analysis status lost implementation_fidelity output path")
        if scores[0]["id"] not in evaluation_md:
            raise AssertionError("IDEA_EVALUATION.md diverged from IDEA_SCORES.json ranking ids")

        print("ok: True")
        print("checks: 10")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root, onerror=remove_readonly)


if __name__ == "__main__":
    raise SystemExit(main())
