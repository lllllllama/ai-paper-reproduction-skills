#!/usr/bin/env python3
"""Regression checks for ai-research-explore orchestration dry runs."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import stat
from pathlib import Path


def write_repo(root: Path) -> None:
    (root / "README.md").write_text(
        "# Demo Research Repo\n\n"
        "## Training\n\n"
        "```bash\n"
        "python train.py --config configs/demo.yaml\n"
        "```\n",
        encoding="utf-8",
    )
    (root / "train.py").write_text("print('train stub')\n", encoding="utf-8")
    (root / "model.py").write_text("class DemoModel:\n    pass\n", encoding="utf-8")
    (root / "environment.yml").write_text("name: demo-env\ndependencies:\n  - python=3.10\n", encoding="utf-8")
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


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    orchestrator = repo_root / "skills" / "ai-research-explore" / "scripts" / "orchestrate_explore.py"

    temp_root = Path(tempfile.mkdtemp(prefix="codex-ai-research-explore-", dir=repo_root))
    try:
        sample_repo = temp_root / "sample_repo"
        sample_repo.mkdir()
        write_repo(sample_repo)
        init_git_repo(sample_repo)

        spec = {
            "current_research": "improved-branch@abc1234",
            "base_command": "python train.py --config configs/demo.yaml",
            "variant_axes": {
                "adapter": ["none", "lora"],
                "lr": ["1e-4", "5e-5"],
            },
            "subset_sizes": [128],
            "short_run_steps": [100, 200],
        }
        spec_path = temp_root / "variant-spec.json"
        spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")

        output_dir = temp_root / "explore_outputs"
        result = subprocess.run(
            [
                sys.executable,
                str(orchestrator),
                "--repo",
                str(sample_repo),
                "--current-research",
                "improved-branch@abc1234",
                "--output-dir",
                str(output_dir),
                "--variant-spec-json",
                str(spec_path),
                "--include-analysis-pass",
                "--include-setup-pass",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(result.stdout)
        expected_chain = [
            "analyze-project",
            "env-and-assets-bootstrap",
            "explore-code",
            "explore-run",
        ]

        if payload["current_research"] != "improved-branch@abc1234":
            raise AssertionError("ai-research-explore lost current_research")
        if payload["planned_skill_chain"] != expected_chain:
            raise AssertionError("ai-research-explore emitted the wrong planned skill chain")
        if payload["variant_count"] != 8:
            raise AssertionError("ai-research-explore emitted the wrong variant_count")
        if payload["workspace"]["mode"] != "worktree":
            raise AssertionError("ai-research-explore did not allocate an isolated worktree for dry-run orchestration")
        if Path(payload["workspace"]["workspace_root"]).resolve() == sample_repo.resolve():
            raise AssertionError("ai-research-explore reused the original checkout during dry-run planning")
        if payload["workspace"]["created_branch"] is not True:
            raise AssertionError("ai-research-explore did not create an isolated experiment branch")
        if not payload["candidate_edit_targets"]:
            raise AssertionError("ai-research-explore failed to produce candidate edit targets")
        if not payload["invoked_stage_trace"]:
            raise AssertionError("ai-research-explore failed to emit a helper stage trace")
        if payload["setup_commands"][0]["command"] != "conda env create -f environment.yml":
            raise AssertionError("ai-research-explore failed to propagate setup commands")
        if payload["setup_commands"][0]["platforms"] != ["windows", "macos", "linux"]:
            raise AssertionError("ai-research-explore lost setup command platform metadata")
        if not payload["recommended_next_trials"]:
            raise AssertionError("ai-research-explore failed to recommend next trials")
        if not payload["analysis_artifacts"]["idea_cards"].endswith("IDEA_CARDS.json"):
            raise AssertionError("ai-research-explore failed to expose analysis artifacts")
        if not payload["sources_index_path"]:
            raise AssertionError("ai-research-explore failed to expose sources index path")
        if not payload["minimal_patch_plan"]:
            raise AssertionError("ai-research-explore failed to expose a minimal patch plan")
        if payload["resource_plan"]["short_run_feasibility"] != "proceed":
            raise AssertionError("ai-research-explore dry-run lost short-run feasibility")
        if payload["researcher_idea_count"] != 0:
            raise AssertionError("ai-research-explore dry-run should not invent researcher ideas")
        if payload["generated_idea_count"] <= 0:
            raise AssertionError("ai-research-explore dry-run did not synthesize bounded seed ideas")
        if payload["selected_idea"]["seed_origin"] != "synthesized":
            raise AssertionError("ai-research-explore dry-run should select from synthesized ideas when no researcher ideas exist")
        if payload["atomic_unit_count"] <= 0:
            raise AssertionError("ai-research-explore dry-run did not produce atomic decomposition output")
        if payload["fidelity_summary"]["unit_count"] <= 0:
            raise AssertionError("ai-research-explore dry-run did not surface implementation fidelity")

        branch_check = subprocess.run(
            ["git", "branch", "--list", payload["experiment_branch"]],
            cwd=sample_repo,
            check=True,
            capture_output=True,
            text=True,
        )
        if payload["experiment_branch"] not in branch_check.stdout:
            raise AssertionError("ai-research-explore failed to create the expected experiment branch")

        for rel in ["CHANGESET.md", "TOP_RUNS.md", "status.json"]:
            if not (output_dir / rel).exists():
                raise AssertionError(f"ai-research-explore dry-run failed to emit {rel}")

        status = json.loads((output_dir / "status.json").read_text(encoding="utf-8"))
        if status["current_research"] != "improved-branch@abc1234":
            raise AssertionError("ai-research-explore status lost current_research")
        if status["planned_skill_chain"] != expected_chain:
            raise AssertionError("ai-research-explore status lost planned skill chain")
        if status["explore_context"]["experiment_branch"] != payload["experiment_branch"]:
            raise AssertionError("ai-research-explore status lost canonical explore_context")
        if not status["helper_stage_trace"]:
            raise AssertionError("ai-research-explore status lost helper stage trace")
        if status["resource_plan"]["short_run_feasibility"] != "proceed":
            raise AssertionError("ai-research-explore status lost resource feasibility")
        if not status["minimal_patch_plan"]:
            raise AssertionError("ai-research-explore status lost minimal patch plan")
        if status["outputs"]["idea_seeds"] != "analysis_outputs/IDEA_SEEDS.json":
            raise AssertionError("ai-research-explore status lost IDEA_SEEDS output")
        if status["outputs"]["atomic_idea_map"] != "analysis_outputs/ATOMIC_IDEA_MAP.json":
            raise AssertionError("ai-research-explore status lost ATOMIC_IDEA_MAP output")
        if status["outputs"]["implementation_fidelity"] != "analysis_outputs/IMPLEMENTATION_FIDELITY.json":
            raise AssertionError("ai-research-explore status lost IMPLEMENTATION_FIDELITY output")
        if status["generated_idea_count"] <= 0 or status["researcher_idea_count"] != 0:
            raise AssertionError("ai-research-explore status lost idea-generation counts")
        if status["atomic_unit_count"] <= 0:
            raise AssertionError("ai-research-explore status lost atomic unit count")
        if status["fidelity_summary"]["unit_count"] <= 0:
            raise AssertionError("ai-research-explore status lost fidelity summary")
        idea_seeds = json.loads((temp_root / "analysis_outputs" / "IDEA_SEEDS.json").read_text(encoding="utf-8"))
        required_seed_fields = {
            "id",
            "summary",
            "seed_origin",
            "context_anchor",
            "task_family_binding",
            "dataset_binding",
            "evaluation_binding",
            "constraint_notes",
        }
        if not idea_seeds["generated_ideas"] or not required_seed_fields.issubset(set(idea_seeds["generated_ideas"][0])):
            raise AssertionError("ai-research-explore dry-run lost IDEA_SEEDS schema fields")

        invalid = subprocess.run(
            [
                sys.executable,
                str(orchestrator),
                "--repo",
                str(sample_repo),
                "--current-research",
                "broken-anchor@not-a-commit",
                "--output-dir",
                str(temp_root / "invalid_outputs"),
            ],
            capture_output=True,
            text=True,
        )
        if invalid.returncode == 0:
            raise AssertionError("ai-research-explore accepted an invalid current_research anchor")

        print("ok: True")
        print("checks: 22")
        print("failures: 0")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root, onerror=remove_readonly)


if __name__ == "__main__":
    raise SystemExit(main())

