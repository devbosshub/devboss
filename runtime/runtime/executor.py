from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


SYSTEM_INSTRUCTIONS = """
You are the Dev Boss engineer runtime.
Read TASK.md, COMMENTS.md, PROJECT_CONTEXT.md, and STAGE_INSTRUCTIONS.md when it is present.
Emit a single JSON object with keys:
- outcome_type
- summary
- branch_name
- pr_url
- deploy_url
- blocked_reason

Use outcome_type from:
needs_human_input, grooming_complete, build_complete, testing_complete, deployment_complete, blocked, failed

Reply with only a single JSON object and no markdown fences.
""".strip()


def _extract_json_object(output: str) -> dict:
    match = re.search(r"\{.*\}", output, re.DOTALL)
    if not match:
        raise json.JSONDecodeError("No JSON object found", output, 0)
    return json.loads(match.group(0))


def run_codex(task_root: Path, codex_command: str, dry_run: bool) -> tuple[dict, str]:
    if dry_run:
        outcome = {
            "outcome_type": "needs_human_input",
            "summary": "Dry-run mode is enabled. Replace with a live Codex CLI invocation to execute the task.",
            "branch_name": None,
            "pr_url": None,
            "deploy_url": None,
            "blocked_reason": "Runtime is configured for dry-run only."
        }
        return outcome, json.dumps(outcome)

    prompt = (
        f"{SYSTEM_INSTRUCTIONS}\n\n"
        "You are operating inside the repository root. "
        "Treat STAGE_INSTRUCTIONS.md as the authoritative guidance for the current execution stage. "
        "Inspect the repository, follow the task files in this directory, act within the limits of the current stage, and then emit the JSON outcome."
    )
    command = [
        codex_command,
        "exec",
        "--skip-git-repo-check",
        "--dangerously-bypass-approvals-and-sandbox",
        prompt,
    ]
    result = subprocess.run(command, cwd=task_root, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        outcome = {
            "outcome_type": "failed",
            "summary": result.stderr or "Codex CLI execution failed",
            "branch_name": None,
            "pr_url": None,
            "deploy_url": None,
            "blocked_reason": None
        }
        return outcome, result.stdout or result.stderr
    try:
        return _extract_json_object(result.stdout), result.stdout
    except json.JSONDecodeError:
        outcome = {
            "outcome_type": "failed",
            "summary": f"Codex output was not valid JSON.\n{result.stdout}",
            "branch_name": None,
            "pr_url": None,
            "deploy_url": None,
            "blocked_reason": None
        }
        return outcome, result.stdout
