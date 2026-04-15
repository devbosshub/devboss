from app import main as main_module
from app.enums import EngineerRuntimeStatus
from app.models import EngineerRuntime


def create_runtime(db_session, engineer_id: int, status: EngineerRuntimeStatus = EngineerRuntimeStatus.HEALTHY) -> EngineerRuntime:
    runtime = EngineerRuntime(
        engineer_id=engineer_id,
        runtime_status=status,
        container_name=f"devboss-engineer-{engineer_id}-test",
        container_id=f"container-{engineer_id}",
    )
    db_session.add(runtime)
    db_session.commit()
    db_session.refresh(runtime)
    return runtime


def test_create_project_and_task_flow(client):
    project_response = client.post(
        "/projects",
        json={
            "name": "Dev Boss Platform",
            "repo_url": "https://github.com/acme/devboss",
            "default_branch": "main",
            "deploy_config": {"strategy": "docker-compose"},
            "engineer_pool": []
        },
    )
    assert project_response.status_code == 200
    project_id = project_response.json()["id"]

    engineers_response = client.get("/engineers")
    assert engineers_response.status_code == 200
    engineer_id = engineers_response.json()[0]["id"]

    task_response = client.post(
        "/tasks",
        json={
            "project_id": project_id,
            "assigned_engineer_id": engineer_id,
            "title": "Set up the dashboard",
            "requirement_markdown": "Need a delivery board for AI tasks.",
            "acceptance_criteria": "Board shows all workflow states.",
            "implementation_steps": "Create UI and backend endpoints.",
            "status": "ai_grooming"
        },
    )
    assert task_response.status_code == 200
    task = task_response.json()
    assert task["status"] == "ai_grooming"
    assert len(task["task_runs"]) == 1

    board_response = client.get("/board")
    assert board_response.status_code == 200
    lanes = {lane["status"]: lane["tasks"] for lane in board_response.json()["lanes"]}
    assert len(lanes["ai_grooming"]) == 1


def test_agent_poll_and_outcome_flow(client, db_session):
    project_id = client.post(
        "/projects",
        json={
            "name": "Runtime Test",
            "repo_url": "https://github.com/acme/runtime",
            "default_branch": "main",
            "deploy_config": {},
            "engineer_pool": []
        },
    ).json()["id"]
    engineer_id = client.get("/engineers").json()[0]["id"]
    task = client.post(
        "/tasks",
        json={
            "project_id": project_id,
            "assigned_engineer_id": engineer_id,
            "title": "Review requirements",
            "requirement_markdown": "Check repo and ask questions.",
            "acceptance_criteria": "Open questions are captured.",
            "implementation_steps": "",
            "status": "ai_grooming"
        },
    ).json()
    task_run_id = task["task_runs"][0]["id"]
    runtime = create_runtime(db_session, engineer_id)

    poll_response = client.post("/agent/poll-next-task", json={"runtime_id": runtime.id})
    assert poll_response.status_code == 200
    payload = poll_response.json()
    assert payload["task"]["id"] == task["id"]
    assert payload["task_run"]["id"] == task_run_id
    assert "TASK.md" in payload["task_bundle"]
    assert "STAGE_INSTRUCTIONS.md" in payload["task_bundle"]
    assert "Do not implement the task." in payload["task_bundle"]["STAGE_INSTRUCTIONS.md"]

    log_response = client.post(
        f"/agent/task-runs/{task_run_id}/logs",
        json={"body": "I need clarification on the API contract.", "author_name": "runtime", "action_required": True},
    )
    assert log_response.status_code == 200

    outcome_response = client.post(
        f"/agent/task-runs/{task_run_id}/outcome",
        json={
            "outcome_type": "needs_human_input",
            "summary": "Need clarification on deployment expectations.",
            "branch_name": None,
            "pr_url": None,
            "deploy_url": None,
            "blocked_reason": None
        },
    )
    assert outcome_response.status_code == 200
    assert outcome_response.json()["status"] == "waiting_human"
    assert outcome_response.json()["outcome_payload_json"]["outcome_type"] == "needs_human_input"

    task_response = client.get(f"/tasks/{task['id']}")
    assert task_response.status_code == 200
    latest_comment = task_response.json()["comments"][-1]
    assert latest_comment["action_required"] is True


def test_ready_to_deploy_requires_human_trigger_before_deployment_and_archives_after_success(client, db_session):
    project_id = client.post(
        "/projects",
        json={
            "name": "Deployment Flow",
            "repo_url": "https://github.com/acme/deployment-flow",
            "default_branch": "main",
            "deploy_config": {"type": "frontend_static_s3"},
            "deployment_instructions": "Build the default branch and deploy it.",
            "engineer_pool": [],
        },
    ).json()["id"]
    engineer_id = client.get("/engineers").json()[0]["id"]
    task = client.post(
        "/tasks",
        json={
            "project_id": project_id,
            "assigned_engineer_id": engineer_id,
            "title": "Ship the release",
            "requirement_markdown": "Prepare the final PR and then deploy after merge.",
            "acceptance_criteria": "PR is created, merged, and deployment is completed.",
            "implementation_steps": "",
            "status": "ready_to_deploy",
        },
    ).json()
    release_prep_run_id = task["task_runs"][0]["id"]
    runtime = create_runtime(db_session, engineer_id)

    poll_release_prep = client.post("/agent/poll-next-task", json={"runtime_id": runtime.id})
    assert poll_release_prep.status_code == 200
    release_prep_payload = poll_release_prep.json()
    assert release_prep_payload["task"]["status"] == "ready_to_deploy"
    assert "pull request" in release_prep_payload["task_bundle"]["STAGE_INSTRUCTIONS.md"].lower()

    pr_ready_response = client.post(
        f"/agent/task-runs/{release_prep_run_id}/outcome",
        json={
            "outcome_type": "deployment_complete",
            "summary": "Task branch is pushed and a PR is ready for human merge.",
            "branch_name": "codex/task-42",
            "pr_url": "https://github.com/acme/deployment-flow/pull/42",
            "deploy_url": None,
            "blocked_reason": None,
        },
    )
    assert pr_ready_response.status_code == 200

    after_pr_task = client.get(f"/tasks/{task['id']}").json()
    assert after_pr_task["status"] == "ready_to_deploy"
    assert after_pr_task["pr_url"] == "https://github.com/acme/deployment-flow/pull/42"
    assert after_pr_task["task_runs"][-1]["status"] == "completed"

    approval_response = client.post(
        f"/task-runs/{release_prep_run_id}/approve",
        json={"summary": "Human merged the PR and triggered deployment."},
    )
    assert approval_response.status_code == 200

    deployment_ready_task = client.get(f"/tasks/{task['id']}").json()
    assert deployment_ready_task["status"] == "deployed"
    assert deployment_ready_task["task_runs"][-1]["status"] == "pending"

    deployment_run_id = deployment_ready_task["task_runs"][-1]["id"]
    poll_deployment = client.post("/agent/poll-next-task", json={"runtime_id": runtime.id})
    assert poll_deployment.status_code == 200
    deployment_payload = poll_deployment.json()
    assert deployment_payload["task"]["status"] == "deployed"
    assert "default branch" in deployment_payload["task_bundle"]["STAGE_INSTRUCTIONS.md"].lower()

    deployment_response = client.post(
        f"/agent/task-runs/{deployment_run_id}/outcome",
        json={
            "outcome_type": "deployment_complete",
            "summary": "Default branch deployment completed successfully.",
            "branch_name": None,
            "pr_url": "https://github.com/acme/deployment-flow/pull/42",
            "deploy_url": "https://app.example.com",
            "blocked_reason": None,
        },
    )
    assert deployment_response.status_code == 200

    archived_task = client.get(f"/tasks/{task['id']}").json()
    assert archived_task["status"] == "archived"
    assert archived_task["deploy_url"] == "https://app.example.com"


def test_release_queue_serializes_ready_to_deploy_and_deployment_per_project(client, db_session):
    project_id = client.post(
        "/projects",
        json={
            "name": "Release Queue",
            "repo_url": "https://github.com/acme/release-queue",
            "default_branch": "main",
            "deploy_config": {"type": "frontend_static_s3"},
            "deployment_instructions": "Prepare PRs and deploy from main.",
            "engineer_pool": [],
        },
    ).json()["id"]
    engineer_id = client.get("/engineers").json()[0]["id"]
    task_one = client.post(
        "/tasks",
        json={
            "project_id": project_id,
            "assigned_engineer_id": engineer_id,
            "title": "Release first",
            "requirement_markdown": "First release candidate.",
            "acceptance_criteria": "Ready first.",
            "implementation_steps": "",
            "status": "ready_to_deploy",
        },
    ).json()
    task_two = client.post(
        "/tasks",
        json={
            "project_id": project_id,
            "assigned_engineer_id": engineer_id,
            "title": "Release second",
            "requirement_markdown": "Second release candidate.",
            "acceptance_criteria": "Ready second.",
            "implementation_steps": "",
            "status": "ready_to_deploy",
        },
    ).json()
    runtime_one = create_runtime(db_session, engineer_id)
    runtime_two = create_runtime(db_session, engineer_id)

    first_poll = client.post("/agent/poll-next-task", json={"runtime_id": runtime_one.id})
    assert first_poll.status_code == 200
    assert first_poll.json()["task"]["id"] == task_one["id"]

    second_poll = client.post("/agent/poll-next-task", json={"runtime_id": runtime_two.id})
    assert second_poll.status_code == 200
    assert second_poll.json()["task_run"] is None

    ready_complete = client.post(
        f"/agent/task-runs/{task_one['task_runs'][0]['id']}/outcome",
        json={
            "outcome_type": "deployment_complete",
            "summary": "PR is ready for merge.",
            "branch_name": "codex/task-one",
            "pr_url": "https://github.com/acme/release-queue/pull/1",
            "deploy_url": None,
            "blocked_reason": None,
        },
    )
    assert ready_complete.status_code == 200

    client.post(
        f"/task-runs/{task_one['task_runs'][0]['id']}/approve",
        json={"summary": "Merged and ready to deploy."},
    )

    deployment_poll = client.post("/agent/poll-next-task", json={"runtime_id": runtime_one.id})
    assert deployment_poll.status_code == 200
    assert deployment_poll.json()["task"]["id"] == task_one["id"]
    assert deployment_poll.json()["task"]["status"] == "deployed"

    still_blocked = client.post("/agent/poll-next-task", json={"runtime_id": runtime_two.id})
    assert still_blocked.status_code == 200
    assert still_blocked.json()["task_run"] is None

    deployment_complete = client.post(
        f"/agent/task-runs/{deployment_poll.json()['task_run']['id']}/outcome",
        json={
            "outcome_type": "deployment_complete",
            "summary": "Deployment completed.",
            "branch_name": None,
            "pr_url": "https://github.com/acme/release-queue/pull/1",
            "deploy_url": "https://release.example.com",
            "blocked_reason": None,
        },
    )
    assert deployment_complete.status_code == 200

    final_poll = client.post("/agent/poll-next-task", json={"runtime_id": runtime_two.id})
    assert final_poll.status_code == 200
    assert final_poll.json()["task"]["id"] == task_two["id"]


def test_manual_archive_from_deployment_stage_frees_release_queue(client, db_session):
    project_id = client.post(
        "/projects",
        json={
            "name": "Manual Archive Release Queue",
            "repo_url": "https://github.com/acme/manual-archive",
            "default_branch": "main",
            "deploy_config": {"type": "frontend_static_s3"},
            "deployment_instructions": "Deploy from main after release approval.",
            "engineer_pool": [],
        },
    ).json()["id"]
    engineer_id = client.get("/engineers").json()[0]["id"]
    task_one = client.post(
        "/tasks",
        json={
            "project_id": project_id,
            "assigned_engineer_id": engineer_id,
            "title": "Release first",
            "requirement_markdown": "Deploy the first release candidate.",
            "acceptance_criteria": "Deployment is completed or manually cleared from the queue.",
            "implementation_steps": "",
            "status": "ready_to_deploy",
        },
    ).json()
    task_two = client.post(
        "/tasks",
        json={
            "project_id": project_id,
            "assigned_engineer_id": engineer_id,
            "title": "Release second",
            "requirement_markdown": "Deploy the second release candidate.",
            "acceptance_criteria": "Deployment can start after the first task leaves the release queue.",
            "implementation_steps": "",
            "status": "ready_to_deploy",
        },
    ).json()
    runtime_one = create_runtime(db_session, engineer_id)
    runtime_two = create_runtime(db_session, engineer_id)
    runtime_three = create_runtime(db_session, engineer_id)

    first_poll = client.post("/agent/poll-next-task", json={"runtime_id": runtime_one.id})
    assert first_poll.status_code == 200
    assert first_poll.json()["task"]["id"] == task_one["id"]

    pr_ready_response = client.post(
        f"/agent/task-runs/{task_one['task_runs'][0]['id']}/outcome",
        json={
            "outcome_type": "deployment_complete",
            "summary": "PR is ready for merge and deployment handoff.",
            "branch_name": "codex/task-32",
            "pr_url": "https://github.com/acme/manual-archive/pull/32",
            "deploy_url": None,
            "blocked_reason": None,
        },
    )
    assert pr_ready_response.status_code == 200

    approval_response = client.post(
        f"/task-runs/{task_one['task_runs'][0]['id']}/approve",
        json={"summary": "Human merged the PR and started deployment."},
    )
    assert approval_response.status_code == 200

    deployment_ready_task = client.get(f"/tasks/{task_one['id']}").json()
    assert deployment_ready_task["status"] == "deployed"

    blocked_poll = client.post("/agent/poll-next-task", json={"runtime_id": runtime_two.id})
    assert blocked_poll.status_code == 200
    assert blocked_poll.json()["task"]["id"] == task_one["id"]
    assert blocked_poll.json()["task"]["status"] == "deployed"

    archive_response = client.patch(f"/tasks/{task_one['id']}", json={"status": "archived"})
    assert archive_response.status_code == 200
    assert archive_response.json()["status"] == "archived"

    next_poll = client.post("/agent/poll-next-task", json={"runtime_id": runtime_three.id})
    assert next_poll.status_code == 200
    assert next_poll.json()["task"]["id"] == task_two["id"]


def test_in_progress_outcome_ignores_pr_url_until_ready_to_deploy(client, db_session):
    project_id = client.post(
        "/projects",
        json={
            "name": "PR Guard",
            "repo_url": "https://github.com/acme/pr-guard",
            "default_branch": "main",
            "deploy_config": {},
            "engineer_pool": [],
        },
    ).json()["id"]
    engineer_id = client.get("/engineers").json()[0]["id"]
    task = client.post(
        "/tasks",
        json={
            "project_id": project_id,
            "assigned_engineer_id": engineer_id,
            "title": "Finish feature branch without opening PR",
            "requirement_markdown": "Implementation should not attach a PR before release prep.",
            "acceptance_criteria": "Task moves to AI testing without a PR URL.",
            "implementation_steps": "",
            "status": "in_progress",
        },
    ).json()
    runtime = create_runtime(db_session, engineer_id)
    run_id = task["task_runs"][0]["id"]

    poll_response = client.post("/agent/poll-next-task", json={"runtime_id": runtime.id})
    assert poll_response.status_code == 200
    assert poll_response.json()["task_run"]["id"] == run_id

    outcome_response = client.post(
        f"/agent/task-runs/{run_id}/outcome",
        json={
            "outcome_type": "build_complete",
            "summary": "Implementation is complete and branch is ready for AI testing.",
            "branch_name": "codex/task-33",
            "pr_url": "https://github.com/acme/pr-guard/pull/33",
            "deploy_url": None,
            "blocked_reason": None,
        },
    )
    assert outcome_response.status_code == 200

    updated_task = client.get(f"/tasks/{task['id']}").json()
    assert updated_task["status"] == "ai_testing"
    assert updated_task["branch_name"] == "codex/task-33"
    assert updated_task["pr_url"] is None


def test_settings_crud(client):
    create_response = client.post(
        "/settings",
        json={
            "key": "github_token",
            "value": "ghp_example",
            "is_secret": True,
            "description": "GitHub token for repo and PR automation"
        },
    )
    assert create_response.status_code == 200
    setting = create_response.json()
    assert setting["key"] == "github_token"

    list_response = client.get("/settings")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = client.patch(
        f"/settings/{setting['id']}",
        json={"value": "ghp_updated", "description": "Updated token"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["value"] == "ghp_updated"


def test_engineer_launch_stop_and_health_ping(client):
    engineer = client.get("/engineers").json()[0]
    client.post(
        "/settings",
        json={
            "key": "codex_auth_json",
            "value": "{\"provider\":\"chatgpt\",\"token\":\"example\"}",
            "is_secret": True,
            "description": "Codex auth file content",
        },
    )
    client.post(
        "/settings",
        json={
            "key": "github_developer_token",
            "value": "ghp_example",
            "is_secret": True,
            "description": "GitHub token for runtime repo checkout",
        },
    )

    class FakeRuntimeManager:
        def launch_engineer(
            self,
            engineer_record,
            runtime_record,
            codex_auth_json,
            github_token,
            aws_access_key_id,
            aws_secret_access_key,
            aws_region,
        ):
            assert codex_auth_json == "{\"provider\":\"chatgpt\",\"token\":\"example\"}"
            assert github_token == "ghp_example"
            assert aws_access_key_id == ""
            assert aws_secret_access_key == ""
            assert aws_region == ""
            return (f"devboss-engineer-{engineer_record.id}-{runtime_record.id}", "container-123")

        def stop_engineer_runtime(self, runtime_record):
            return None

    original_runtime_manager = main_module.runtime_manager
    main_module.runtime_manager = FakeRuntimeManager()
    try:
        launch_response = client.post(f"/engineers/{engineer['id']}/launch")
        assert launch_response.status_code == 200
        launched = launch_response.json()
        assert launched["runtime_status"] == "starting"
        runtime_id = launched["runtimes"][0]["id"]
        assert launched["runtime_container_name"] == f"devboss-engineer-{engineer['id']}-{runtime_id}"

        heartbeat_response = client.post(
            f"/engineer-runtimes/{runtime_id}/heartbeat",
            json={
                "container_name": f"devboss-engineer-{engineer['id']}-{runtime_id}",
                "container_id": "container-123",
                "status_message": "Runtime heartbeat received from engineer container.",
            },
        )
        assert heartbeat_response.status_code == 200
        heartbeat = heartbeat_response.json()
        assert heartbeat["runtime_status"] == "healthy"
        assert heartbeat["last_heartbeat_at"] is not None

        stop_response = client.post(f"/engineer-runtimes/{runtime_id}/stop")
        assert stop_response.status_code == 200
        stopped = stop_response.json()
        assert stopped["runtime_status"] == "stopped"
        assert stopped["container_name"] is None
    finally:
        main_module.runtime_manager = original_runtime_manager


def test_launch_engineer_reuses_latest_stopped_runtime(client, db_session):
    engineer = client.get("/engineers").json()[0]
    stopped_runtime = create_runtime(db_session, engineer["id"], EngineerRuntimeStatus.STOPPED)

    client.post(
        "/settings",
        json={
            "key": "codex_auth_json",
            "value": "{\"provider\":\"chatgpt\",\"token\":\"example\"}",
            "is_secret": True,
            "description": "Codex auth file content",
        },
    )
    client.post(
        "/settings",
        json={
            "key": "github_developer_token",
            "value": "ghp_example",
            "is_secret": True,
            "description": "GitHub token for runtime repo checkout",
        },
    )

    class FakeRuntimeManager:
        def launch_engineer(
            self,
            engineer_record,
            runtime_record,
            codex_auth_json,
            github_token,
            aws_access_key_id,
            aws_secret_access_key,
            aws_region,
        ):
            assert runtime_record.id == stopped_runtime.id
            return (f"devboss-engineer-{engineer_record.id}-{runtime_record.id}", "container-reused")

        def stop_engineer_runtime(self, runtime_record):
            return None

    original_runtime_manager = main_module.runtime_manager
    main_module.runtime_manager = FakeRuntimeManager()
    try:
        launch_response = client.post(f"/engineers/{engineer['id']}/launch")
        assert launch_response.status_code == 200
        launched = launch_response.json()
        assert launched["runtime_count"] == 1
        assert launched["runtimes"][0]["id"] == stopped_runtime.id
        assert launched["runtimes"][0]["runtime_status"] == "starting"
        assert launched["runtime_container_name"] == f"devboss-engineer-{engineer['id']}-{stopped_runtime.id}"
    finally:
        main_module.runtime_manager = original_runtime_manager


def test_delete_engineer_blocks_when_running_and_when_referenced(client):
    create_response = client.post(
        "/engineers",
        json={
            "name": "Delete Me",
            "template": "backend_engineer",
            "skill_markdown": "# Backend",
            "model_name": "gpt-5.4",
            "docker_image": "devboss-engineer:latest",
            "poll_interval_seconds": 30,
            "enabled_tools": ["git"],
            "allowed_projects": [],
            "runtime_config": {},
            "is_active": True,
        },
    )
    assert create_response.status_code == 200
    engineer_id = create_response.json()["id"]

    class FakeRuntimeManager:
        def launch_engineer(
            self,
            engineer_record,
            runtime_record,
            codex_auth_json,
            github_token,
            aws_access_key_id,
            aws_secret_access_key,
            aws_region,
        ):
            return (f"devboss-engineer-{engineer_record.id}-{runtime_record.id}", "container-123")

        def stop_engineer_runtime(self, runtime_record):
            return None

    original_runtime_manager = main_module.runtime_manager
    main_module.runtime_manager = FakeRuntimeManager()
    try:
        client.post(
            "/settings",
            json={
                "key": "codex_auth_json",
                "value": "{\"provider\":\"chatgpt\",\"token\":\"example\"}",
                "is_secret": True,
                "description": "Codex auth file content",
            },
        )
        client.post(
            "/settings",
            json={
                "key": "github_developer_token",
                "value": "ghp_example",
                "is_secret": True,
                "description": "GitHub token for runtime repo checkout",
            },
        )
        launch_response = client.post(f"/engineers/{engineer_id}/launch")
        assert launch_response.status_code == 200

        delete_response = client.delete(f"/engineers/{engineer_id}")
        assert delete_response.status_code == 400
        assert delete_response.json()["detail"] == "Cannot delete a running engineer. Stop the runtime first."

        stop_response = client.post(f"/engineers/{engineer_id}/stop")
        assert stop_response.status_code == 200

        delete_response = client.delete(f"/engineers/{engineer_id}")
        assert delete_response.status_code == 200
        assert delete_response.json() == {"deleted": True}

        project_id = client.post(
            "/projects",
            json={
                "name": "Engineer Delete Guard",
                "repo_url": "https://github.com/acme/delete-guard",
                "default_branch": "main",
                "deploy_config": {},
                "engineer_pool": [],
            },
        ).json()["id"]
        reused_engineer_id = client.get("/engineers").json()[0]["id"]
        task_response = client.post(
            "/tasks",
            json={
                "project_id": project_id,
                "assigned_engineer_id": reused_engineer_id,
                "title": "Assigned task",
                "requirement_markdown": "Do work",
                "acceptance_criteria": "Done",
                "implementation_steps": "",
                "status": "ai_grooming",
            },
        )
        assert task_response.status_code == 200

        blocked_delete = client.delete(f"/engineers/{reused_engineer_id}")
        assert blocked_delete.status_code == 400
    finally:
        main_module.runtime_manager = original_runtime_manager


def test_human_reply_requeues_waiting_task_run(client, db_session):
    project_id = client.post(
        "/projects",
        json={
            "name": "Resume Test",
            "repo_url": "https://github.com/acme/resume",
            "default_branch": "main",
            "deploy_config": {},
            "engineer_pool": [],
        },
    ).json()["id"]
    engineer_id = client.get("/engineers").json()[0]["id"]
    task = client.post(
        "/tasks",
        json={
            "project_id": project_id,
            "assigned_engineer_id": engineer_id,
            "title": "Clarify edge cases",
            "requirement_markdown": "Review the repo and identify any missing decisions.",
            "acceptance_criteria": "Questions are posted back for human review.",
            "implementation_steps": "",
            "status": "ai_grooming",
        },
    ).json()
    task_run_id = task["task_runs"][0]["id"]
    runtime = create_runtime(db_session, engineer_id)

    poll_response = client.post("/agent/poll-next-task", json={"runtime_id": runtime.id})
    assert poll_response.status_code == 200
    outcome_response = client.post(
        f"/agent/task-runs/{task_run_id}/outcome",
        json={
            "outcome_type": "needs_human_input",
            "summary": "Need clarification on rollout expectations.",
            "branch_name": None,
            "pr_url": None,
            "deploy_url": None,
            "blocked_reason": None,
        },
    )
    assert outcome_response.status_code == 200
    assert outcome_response.json()["status"] == "waiting_human"

    comment_response = client.post(
        f"/tasks/{task['id']}/comments",
        json={
            "author_type": "human",
            "author_name": "Human Reviewer",
            "body": "Proceed with the default dev rollout flow.",
            "action_required": False,
        },
    )
    assert comment_response.status_code == 200

    task_response = client.get(f"/tasks/{task['id']}")
    assert task_response.status_code == 200
    latest_run = task_response.json()["task_runs"][-1]
    assert latest_run["status"] == "pending"

    repoll_response = client.post("/agent/poll-next-task", json={"runtime_id": runtime.id})
    assert repoll_response.status_code == 200
    assert repoll_response.json()["task_run"]["id"] == task_run_id


def test_retry_delete_comment_and_delete_task(client, db_session):
    project_id = client.post(
        "/projects",
        json={
            "name": "Task Controls",
            "repo_url": "https://github.com/acme/task-controls",
            "default_branch": "main",
            "deploy_config": {},
            "engineer_pool": [],
        },
    ).json()["id"]
    engineer_id = client.get("/engineers").json()[0]["id"]
    task = client.post(
        "/tasks",
        json={
            "project_id": project_id,
            "assigned_engineer_id": engineer_id,
            "title": "Retryable task",
            "requirement_markdown": "Need a retry control.",
            "acceptance_criteria": "Task can be re-queued and cleaned up.",
            "implementation_steps": "",
            "status": "ai_grooming",
        },
    ).json()
    task_run_id = task["task_runs"][0]["id"]
    runtime = create_runtime(db_session, engineer_id)

    poll_response = client.post("/agent/poll-next-task", json={"runtime_id": runtime.id})
    assert poll_response.status_code == 200
    assert poll_response.json()["task_run"]["id"] == task_run_id

    failed_response = client.post(
        f"/agent/task-runs/{task_run_id}/outcome",
        json={
            "outcome_type": "failed",
            "summary": "Simulated failure",
            "branch_name": None,
            "pr_url": None,
            "deploy_url": None,
            "blocked_reason": "Simulated failure",
        },
    )
    assert failed_response.status_code == 200

    retry_response = client.post(f"/tasks/{task['id']}/retry")
    assert retry_response.status_code == 200
    retried_task = retry_response.json()
    assert retried_task["status"] == "ai_grooming"
    assert retried_task["task_runs"][-1]["status"] == "pending"

    comment_response = client.post(
        f"/tasks/{task['id']}/comments",
        json={
            "author_type": "human",
            "author_name": "Human Reviewer",
            "body": "Temporary note",
            "action_required": False,
        },
    )
    assert comment_response.status_code == 200
    comment_id = comment_response.json()["id"]

    delete_comment_response = client.delete(f"/tasks/{task['id']}/comments/{comment_id}")
    assert delete_comment_response.status_code == 200
    assert delete_comment_response.json()["deleted"] is True

    task_after_comment_delete = client.get(f"/tasks/{task['id']}")
    assert all(comment["id"] != comment_id for comment in task_after_comment_delete.json()["comments"])

    delete_task_response = client.delete(f"/tasks/{task['id']}")
    assert delete_task_response.status_code == 200
    assert delete_task_response.json()["deleted"] is True

    missing_task_response = client.get(f"/tasks/{task['id']}")
    assert missing_task_response.status_code == 404


def test_ai_testing_failure_loops_back_to_in_progress_until_human_pause(client, db_session):
    project_id = client.post(
        "/projects",
        json={
            "name": "AI Testing Loop",
            "repo_url": "https://github.com/acme/testing-loop",
            "default_branch": "main",
            "deploy_config": {},
            "engineer_pool": [],
        },
    ).json()["id"]
    engineer_id = client.get("/engineers").json()[0]["id"]
    task = client.post(
        "/tasks",
        json={
            "project_id": project_id,
            "assigned_engineer_id": engineer_id,
            "title": "Fix flaky settings page",
            "requirement_markdown": "Testing should send implementation back when it finds issues.",
            "acceptance_criteria": "Auto-loop from testing to build is capped.",
            "implementation_steps": "",
            "status": "ai_testing",
        },
    ).json()
    runtime = create_runtime(db_session, engineer_id)

    for expected_loop in range(1, 4):
        current_run_id = task["task_runs"][-1]["id"]
        poll_response = client.post("/agent/poll-next-task", json={"runtime_id": runtime.id})
        assert poll_response.status_code == 200
        assert poll_response.json()["task_run"]["id"] == current_run_id

        outcome_response = client.post(
            f"/agent/task-runs/{current_run_id}/outcome",
            json={
                "outcome_type": "failed",
                "summary": f"Testing found regression #{expected_loop}",
                "branch_name": None,
                "pr_url": None,
                "deploy_url": None,
                "blocked_reason": f"Regression details #{expected_loop}",
            },
        )
        assert outcome_response.status_code == 200

        task_response = client.get(f"/tasks/{task['id']}")
        assert task_response.status_code == 200
        task = task_response.json()
        assert task["status"] == "in_progress"
        assert task["testing_rework_count"] == expected_loop
        assert any(comment["author_name"] == "ai-testing" for comment in task["comments"])
        assert task["task_runs"][-1]["phase"] == "build"
        assert task["task_runs"][-1]["status"] == "pending"

        client.post(
            f"/agent/task-runs/{task['task_runs'][-1]['id']}/outcome",
            json={
                "outcome_type": "build_complete",
                "summary": f"Implemented fix #{expected_loop}",
                "branch_name": None,
                "pr_url": None,
                "deploy_url": None,
                "blocked_reason": None,
            },
        )
        task = client.get(f"/tasks/{task['id']}").json()
        assert task["status"] == "ai_testing"

    final_testing_run_id = task["task_runs"][-1]["id"]
    poll_response = client.post("/agent/poll-next-task", json={"runtime_id": runtime.id})
    assert poll_response.status_code == 200
    assert poll_response.json()["task_run"]["id"] == final_testing_run_id

    final_outcome_response = client.post(
        f"/agent/task-runs/{final_testing_run_id}/outcome",
        json={
            "outcome_type": "failed",
            "summary": "Testing still fails after repeated implementation attempts",
            "branch_name": None,
            "pr_url": None,
            "deploy_url": None,
            "blocked_reason": "Need human guidance on the root cause",
        },
    )
    assert final_outcome_response.status_code == 200
    assert final_outcome_response.json()["status"] == "waiting_human"

    final_task = client.get(f"/tasks/{task['id']}").json()
    assert final_task["status"] == "ai_testing"
    assert final_task["testing_rework_count"] == 3
    assert final_task["blocked_reason"] == "Need human guidance on the root cause"
    assert final_task["comments"][-1]["action_required"] is True
