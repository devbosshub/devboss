from __future__ import annotations

import threading
import time
from socket import gethostname

from runtime.client import DevBossClient
from runtime.config import RuntimeSettings
from runtime.executor import run_codex
from runtime.github import create_or_get_pull_request
from runtime.task_bundle import write_task_bundle
from runtime.workspace import ensure_task_branch, persist_branch_changes, prepare_repo_workspace

ALLOWED_OUTCOMES_BY_STATUS = {
    "ai_grooming": {"needs_human_input", "grooming_complete", "blocked", "failed"},
    "in_progress": {"needs_human_input", "build_complete", "blocked", "failed"},
    "ai_testing": {"needs_human_input", "testing_complete", "blocked", "failed"},
    "ready_to_deploy": {"needs_human_input", "deployment_complete", "blocked", "failed"},
    "deployed": {"needs_human_input", "deployment_complete", "blocked", "failed"},
}
PR_URL_ALLOWED_STATUSES = {"ready_to_deploy", "deployed"}


def truncate_output(output: str, limit: int = 6000) -> str:
    if len(output) <= limit:
        return output
    return f"{output[:limit]}\n\n[truncated]"


def build_human_readable_comment(task: dict, outcome: dict) -> str:
    lines = [
        f"## Task Update",
        "",
        f"**Task:** #{task['id']} - {task['title']}",
        f"**Outcome:** {outcome['outcome_type'].replace('_', ' ').title()}",
        "",
        "### Summary",
        "",
        outcome["summary"],
    ]

    details: list[str] = []
    if outcome.get("blocked_reason"):
        details.append(f"- **Blocked reason:** {outcome['blocked_reason']}")
    if outcome.get("branch_name"):
        details.append(f"- **Branch:** `{outcome['branch_name']}`")
        if outcome["outcome_type"] == "build_complete":
            details.append("- **Branch handoff:** Implementation is complete and this branch has been pushed for AI Testing to continue from the same code state.")
        elif outcome["outcome_type"] == "testing_complete":
            details.append("- **Branch handoff:** AI Testing ran against this branch, so later stages should continue from the same branch state.")
    if outcome.get("pr_url"):
        details.append(f"- **Pull request:** {outcome['pr_url']}")
    if outcome.get("deploy_url"):
        details.append(f"- **Deploy URL:** {outcome['deploy_url']}")
    if details:
        lines.extend(["", "### Details", "", *details])
    if outcome["outcome_type"] == "needs_human_input":
        lines.extend(
            [
                "",
                "### Action Needed",
                "",
                "Please reply on this task thread with the missing information or decision. The engineer will pick the task up again from your reply.",
            ]
        )

    return "\n".join(lines)


def branch_to_clone(task: dict, project: dict) -> str:
    if task["status"] == "deployed":
        return project["default_branch"]
    branch_name = task.get("branch_name")
    if task["status"] == "in_progress":
        return branch_name if branch_name and branch_name != project["default_branch"] else project["default_branch"]
    return branch_name or project["default_branch"]


def normalize_outcome_for_task(task: dict, outcome: dict) -> dict:
    allowed_outcomes = ALLOWED_OUTCOMES_BY_STATUS.get(task["status"], set())
    if outcome["outcome_type"] in allowed_outcomes:
        if task["status"] not in PR_URL_ALLOWED_STATUSES:
            outcome["pr_url"] = None
        return outcome
    allowed_list = ", ".join(sorted(allowed_outcomes)) or "none"
    return {
        "outcome_type": "failed",
        "summary": (
            f"Codex returned outcome '{outcome['outcome_type']}' for task status '{task['status']}', "
            f"which is not allowed. Allowed outcomes: {allowed_list}. Original summary: {outcome.get('summary', '')}"
        ).strip(),
        "branch_name": outcome.get("branch_name"),
        "pr_url": outcome.get("pr_url"),
        "deploy_url": outcome.get("deploy_url"),
        "blocked_reason": f"Invalid stage outcome from Codex: {outcome['outcome_type']} for task status {task['status']}.",
    }


def start_heartbeat_loop(
    client: DevBossClient,
    settings: RuntimeSettings,
    container_id: str,
    task_run_id: int | None = None,
) -> tuple[threading.Event, threading.Thread]:
    stop_event = threading.Event()

    def heartbeat() -> None:
        while not stop_event.is_set():
            client.engineer_heartbeat(
                settings.runtime_id,
                container_name=settings.effective_container_name,
                container_id=container_id,
                status_message="Engineer runtime is active.",
            )
            if task_run_id is not None:
                client.heartbeat(task_run_id, "Codex execution in progress")
            stop_event.wait(settings.heartbeat_interval_seconds)

    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()
    return stop_event, thread


def run_loop() -> None:
    settings = RuntimeSettings()
    client = DevBossClient(settings.api_base_url)
    container_id = gethostname()

    while True:
        client.engineer_heartbeat(
            settings.runtime_id,
            container_name=settings.effective_container_name,
            container_id=container_id,
            status_message="Runtime heartbeat received from engineer container.",
        )

        if settings.heartbeat_only:
            time.sleep(settings.heartbeat_interval_seconds)
            continue

        payload = client.poll_next_task(settings.runtime_id)
        task_run = payload.get("task_run")
        task = payload.get("task")

        if not task_run or not task:
            time.sleep(settings.poll_interval_seconds)
            continue

        heartbeat_stop, heartbeat_thread = start_heartbeat_loop(client, settings, container_id, task_run["id"])
        try:
            repo_root = prepare_repo_workspace(
                settings.workspace_path,
                task["id"],
                payload["project"]["repo_url"],
                branch_to_clone(task, payload["project"]),
                settings.github_token,
            )
            branch_name = ensure_task_branch(
                repo_root,
                task["id"],
                task["status"],
                task.get("branch_name"),
                payload["project"]["default_branch"],
            )
            task_root = write_task_bundle(repo_root, payload["task_bundle"])
            client.post_log(
                task_run["id"],
                f"Claimed task #{task['id']}, cleaned workspace, checked out the repository into {repo_root}, and prepared branch `{branch_name}`.",
            )
            client.heartbeat(task_run["id"], "Starting Codex execution")
            outcome, _raw_output = run_codex(task_root, settings.codex_command, settings.dry_run)
            outcome = normalize_outcome_for_task(task, outcome)
            outcome["branch_name"] = None if task["status"] in {"ai_grooming", "deployed"} else branch_name

            if outcome["outcome_type"] in {"build_complete", "testing_complete"} or (
                outcome["outcome_type"] == "deployment_complete" and task["status"] == "ready_to_deploy"
            ):
                persist_branch_changes(
                    repo_root,
                    branch_name,
                    f"Dev Boss task {task['id']}: {outcome['outcome_type'].replace('_', ' ')}",
                )

            if outcome["outcome_type"] == "deployment_complete" and task["status"] == "ready_to_deploy":
                pr_url = create_or_get_pull_request(
                    payload["project"]["repo_url"],
                    settings.github_token,
                    branch_name,
                    payload["project"]["default_branch"],
                    f"Task #{task['id']}: {task['title']}",
                    outcome["summary"],
                )
                outcome["pr_url"] = pr_url

            client.post_log(
                task_run["id"],
                build_human_readable_comment(task, outcome),
                action_required=outcome["outcome_type"] in {"needs_human_input", "blocked", "failed"},
            )
            client.post_outcome(task_run["id"], outcome)
        except Exception as exc:
            error_text = str(exc) or "Runtime execution failed."
            client.post_log(task_run["id"], f"Runtime error:\n\n{error_text}", action_required=True)
            client.post_outcome(
                task_run["id"],
                {
                    "outcome_type": "failed",
                    "summary": error_text,
                    "branch_name": None,
                    "pr_url": None,
                    "deploy_url": None,
                    "blocked_reason": error_text,
                },
            )
        finally:
            heartbeat_stop.set()
            heartbeat_thread.join(timeout=2)
        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    run_loop()
