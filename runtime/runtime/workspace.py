from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit


def _clone_url(repo_url: str, github_token: str) -> str:
    if not github_token or "github.com" not in repo_url:
        return repo_url
    parts = urlsplit(repo_url)
    if parts.scheme not in {"http", "https"}:
        return repo_url
    netloc = f"x-access-token:{quote(github_token, safe='')}@{parts.netloc}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def _run_git(repo_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"Git command failed: {' '.join(args)}")
    return result


def prepare_repo_workspace(
    workspace_dir: Path,
    task_id: int,
    repo_url: str,
    clone_branch: str,
    github_token: str,
) -> Path:
    task_root = workspace_dir / f"task-{task_id}"
    if task_root.exists():
        shutil.rmtree(task_root)
    task_root.mkdir(parents=True, exist_ok=True)

    repo_root = task_root / "repo"
    clone_command = [
        "git",
        "clone",
        "--depth",
        "1",
        "--branch",
        clone_branch,
        _clone_url(repo_url, github_token),
        str(repo_root),
    ]
    clone_error = "Failed to clone repository."
    for attempt in range(3):
        result = subprocess.run(clone_command, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return repo_root

        clone_error = result.stderr.strip() or clone_error
        is_transient_network_error = any(
            marker in clone_error.lower()
            for marker in {
                "could not resolve host",
                "temporary failure in name resolution",
                "network is unreachable",
                "connection timed out",
            }
        )
        if not is_transient_network_error or attempt == 2:
            break
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(clone_error)


def ensure_task_branch(
    repo_root: Path,
    task_id: int,
    task_status: str,
    existing_branch_name: str | None,
    default_branch: str,
) -> str:
    if task_status == "in_progress":
        branch_name = (
            existing_branch_name
            if existing_branch_name and existing_branch_name != default_branch
            else f"codex/task-{task_id}"
        )
        _run_git(repo_root, ["checkout", "-B", branch_name])
        return branch_name

    if task_status == "deployed":
        _run_git(repo_root, ["checkout", default_branch])
        return default_branch

    if existing_branch_name:
        _run_git(repo_root, ["checkout", existing_branch_name])
        return existing_branch_name

    return _run_git(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()


def persist_branch_changes(repo_root: Path, branch_name: str, commit_message: str) -> bool:
    status = _run_git(repo_root, ["status", "--porcelain"]).stdout.strip()
    if status:
        _run_git(repo_root, ["config", "user.name", "Dev Boss"])
        _run_git(repo_root, ["config", "user.email", "devboss@local"])
        _run_git(repo_root, ["add", "-A"])

        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if commit_result.returncode != 0 and "nothing to commit" not in (commit_result.stdout + commit_result.stderr).lower():
            raise RuntimeError(commit_result.stderr.strip() or "Failed to commit task branch changes.")

    _run_git(repo_root, ["push", "-u", "origin", branch_name])
    return bool(status)
