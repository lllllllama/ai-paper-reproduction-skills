#!/usr/bin/env python3
"""Execute a short non-training command and normalize the evidence."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


METRIC_RE = re.compile(
    r"\b([A-Za-z][A-Za-z0-9_.-]{1,31})\s*[:=]\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)"
)


def combine_logs(parts: Iterable[str]) -> str:
    return "\n".join(part for part in parts if part).strip()


def parse_metrics(text: str) -> Dict[str, Any]:
    observed_metrics: Dict[str, float] = {}
    best_metric: Optional[Dict[str, Any]] = None

    for match in METRIC_RE.finditer(text):
        name = match.group(1)
        value = float(match.group(2))
        observed_metrics[name] = value

    priority_names = [
        name for name in observed_metrics
        if not any(token in name.lower() for token in {"loss", "lr", "time", "mem"})
    ]
    if priority_names:
        chosen = priority_names[-1]
        best_metric = {"name": chosen, "value": observed_metrics[chosen]}
    elif observed_metrics:
        chosen = list(observed_metrics)[-1]
        best_metric = {"name": chosen, "value": observed_metrics[chosen]}

    return {
        "observed_metrics": observed_metrics,
        "best_metric": best_metric,
    }


def split_command(command: str) -> List[str]:
    return shlex.split(command, posix=True)


def execute_command(repo: Path, command: str, timeout: int) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            split_command(command),
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "returncode": result.returncode,
            "timed_out": False,
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
        }
    except FileNotFoundError as exc:
        return {
            "returncode": None,
            "timed_out": False,
            "launch_error": str(exc),
            "stdout": "",
            "stderr": "",
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "returncode": None,
            "timed_out": True,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
        }


def decide_outcome(command: str, timeout: int, execution: Dict[str, Any], metric_data: Dict[str, Any]) -> Dict[str, Any]:
    combined_text = combine_logs(
        [
            f"STDOUT:\n{execution['stdout'].strip()}" if execution.get("stdout", "").strip() else "",
            f"STDERR:\n{execution['stderr'].strip()}" if execution.get("stderr", "").strip() else "",
        ]
    )

    if execution.get("launch_error"):
        return {
            "status": "blocked",
            "documented_command_status": "blocked",
            "main_blocker": f"Executable not found for command: {execution['launch_error']}",
            "execution_log": [f"Command failed before launch: {execution['launch_error']}"],
            "monitoring_scope": "no_run",
        }

    if execution.get("timed_out"):
        return {
            "status": "partial",
            "documented_command_status": "partial",
            "main_blocker": f"Selected command did not finish within {timeout} seconds.",
            "execution_log": [combined_text or f"Command timed out after {timeout} seconds."],
            "monitoring_scope": f"timeout:{timeout}s",
        }

    if execution.get("returncode") == 0:
        return {
            "status": "success",
            "documented_command_status": "success",
            "main_blocker": "None.",
            "execution_log": [combined_text] if combined_text else [],
            "monitoring_scope": "process_completion",
        }

    return {
        "status": "partial",
        "documented_command_status": "partial",
        "main_blocker": f"Selected command exited with code {execution.get('returncode')}.",
        "execution_log": [combined_text] if combined_text else [f"Command `{command}` exited non-zero."],
        "monitoring_scope": "process_completion",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a short non-training command and summarize the evidence.")
    parser.add_argument("--repo", required=True, help="Path to the target repository.")
    parser.add_argument("--command", required=True, help="Command to execute.")
    parser.add_argument("--timeout", type=int, default=60, help="Execution timeout in seconds.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    execution = execute_command(repo, args.command, args.timeout)
    metric_data = parse_metrics(combine_logs([execution.get("stdout", ""), execution.get("stderr", "")]))
    outcome = decide_outcome(args.command, args.timeout, execution, metric_data)

    payload = {
        "status": outcome["status"],
        "documented_command_status": outcome["documented_command_status"],
        "main_blocker": outcome["main_blocker"],
        "execution_log": outcome["execution_log"],
        "monitoring_scope": outcome["monitoring_scope"],
        "best_metric": metric_data["best_metric"],
        "observed_metrics": metric_data["observed_metrics"],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
