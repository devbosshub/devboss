from __future__ import annotations

from urllib.parse import urlsplit

import httpx


def parse_github_repo(repo_url: str) -> tuple[str, str]:
    normalized = repo_url.strip()
    if normalized.endswith(".git"):
        normalized = normalized[:-4]

    if normalized.startswith("git@github.com:"):
        path = normalized.split(":", 1)[1]
    else:
        parts = urlsplit(normalized)
        if "github.com" not in parts.netloc:
            raise RuntimeError(f"Unsupported repository host for PR creation: {repo_url}")
        path = parts.path.lstrip("/")

    segments = [segment for segment in path.split("/") if segment]
    if len(segments) < 2:
        raise RuntimeError(f"Could not parse GitHub repository from URL: {repo_url}")
    return segments[0], segments[1]


def create_or_get_pull_request(
    repo_url: str,
    github_token: str,
    branch_name: str,
    base_branch: str,
    title: str,
    body: str,
) -> str:
    if not github_token:
        raise RuntimeError("GitHub token is missing. Cannot create a pull request.")

    owner, repo = parse_github_repo(repo_url)
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    head_ref = f"{owner}:{branch_name}"

    with httpx.Client(base_url="https://api.github.com", headers=headers, timeout=30.0) as client:
        response = client.post(
            f"/repos/{owner}/{repo}/pulls",
            json={
                "title": title,
                "body": body,
                "head": head_ref,
                "base": base_branch,
            },
        )

        if response.status_code == 201:
            return response.json()["html_url"]

        if response.status_code == 422:
            existing = client.get(
                f"/repos/{owner}/{repo}/pulls",
                params={
                    "state": "open",
                    "head": head_ref,
                    "base": base_branch,
                },
            )
            existing.raise_for_status()
            items = existing.json()
            if items:
                return items[0]["html_url"]

        response.raise_for_status()
        raise RuntimeError("GitHub pull request creation failed unexpectedly.")
