from app.enums import EngineerTemplate, TaskStatus
from app.models import Engineer, Project, Task


DEFAULT_ENGINEERS = [
    {
        "name": "Backend Engineer",
        "template": EngineerTemplate.BACKEND,
        "skill_markdown": "# Backend Engineer\n\nOwns API, schema, integrations, and tests.",
        "enabled_tools": ["python", "git", "tests"],
    },
    {
        "name": "Frontend Engineer",
        "template": EngineerTemplate.FRONTEND,
        "skill_markdown": "# Frontend Engineer\n\nOwns dashboard UX, React, and state management.",
        "enabled_tools": ["node", "git", "ui-tests"],
    },
    {
        "name": "QA/Test Engineer",
        "template": EngineerTemplate.QA,
        "skill_markdown": "# QA/Test Engineer\n\nOwns verification plans and evidence capture.",
        "enabled_tools": ["python", "node", "tests"],
    },
    {
        "name": "DevOps/Deployment Engineer",
        "template": EngineerTemplate.DEVOPS,
        "skill_markdown": "# DevOps/Deployment Engineer\n\nOwns deploy scripts, health checks, and runtime ops.",
        "enabled_tools": ["docker", "git", "shell"],
    },
]


DEMO_PROJECTS = [
    {
        "name": "Acme Customer Portal",
        "repo_url": "https://github.com/acme/customer-portal",
        "default_branch": "main",
        "deploy_config": {"strategy": "docker-compose", "healthcheck_path": "/health"},
        "tasks": [
            {
                "title": "Finalize onboarding requirements",
                "requirement_markdown": "Document the onboarding experience and capture missing questions before implementation starts.",
                "acceptance_criteria": "Requirements are clear, open questions are visible, and the task is ready for build approval.",
                "implementation_steps": "Review repo, inspect auth flows, and collect unresolved requirements.",
                "status": TaskStatus.AI_GROOMING,
                "assigned_engineer_index": 0,
            },
            {
                "title": "Build settings management screen",
                "requirement_markdown": "Implement a page for workspace-level settings including GitHub and AWS credentials.",
                "acceptance_criteria": "Users can create and review tool-wide settings in the dashboard.",
                "implementation_steps": "Add backend config storage, API endpoints, and a frontend settings page.",
                "status": TaskStatus.IN_PROGRESS,
                "assigned_engineer_index": 1,
                "branch_name": "feature/settings-page",
                "pr_url": "https://github.com/acme/customer-portal/pull/42",
            },
            {
                "title": "Verify dashboard workflow states",
                "requirement_markdown": "Validate that each SDLC lane renders correctly and attach screenshots for evidence.",
                "acceptance_criteria": "Test evidence exists for all statuses and issues are documented.",
                "implementation_steps": "Run UI checks, capture evidence, and summarize findings.",
                "status": TaskStatus.AI_TESTING,
                "assigned_engineer_index": 2,
            },
            {
                "title": "Approve dev deployment for notifications",
                "requirement_markdown": "Human needs to validate the notifications service in the dev environment.",
                "acceptance_criteria": "Reviewer can access the service in dev and confirm expected behavior.",
                "implementation_steps": "Deploy branch to dev and share endpoint with reviewer.",
                "status": TaskStatus.HUMAN_TESTING,
                "assigned_engineer_index": 3,
                "deploy_url": "https://dev.acme.local/notifications",
            },
            {
                "title": "Merge analytics update",
                "requirement_markdown": "Deployment-ready analytics changes are waiting on final approval.",
                "acceptance_criteria": "Changes are merged and deployed after approval.",
                "implementation_steps": "Review final evidence and merge to main.",
                "status": TaskStatus.READY_TO_DEPLOY,
                "assigned_engineer_index": 3,
                "pr_url": "https://github.com/acme/customer-portal/pull/41",
            },
            {
                "title": "Handle billing export edge case",
                "requirement_markdown": "Billing export flow is blocked on a missing third-party API contract.",
                "acceptance_criteria": "Blocker is visible and task stays paused until the vendor responds.",
                "implementation_steps": "Document blocker and await API clarification.",
                "status": TaskStatus.READY_FOR_BUILD,
                "assigned_engineer_index": 0,
                "blocked_reason": "Waiting on vendor API schema confirmation for export payload fields.",
            },
        ],
    },
    {
        "name": "Orion DevOps Console",
        "repo_url": "https://github.com/acme/orion-devops-console",
        "default_branch": "main",
        "deploy_config": {"strategy": "docker-compose", "healthcheck_path": "/status"},
        "tasks": [
            {
                "title": "Draft observability migration plan",
                "requirement_markdown": "Prepare the rollout plan for moving service logs into the new observability pipeline.",
                "acceptance_criteria": "Requirements and phased rollout steps are captured for implementation.",
                "implementation_steps": "Review current log stack and map migration phases.",
                "status": TaskStatus.DRAFT,
                "assigned_engineer_index": 0,
            },
            {
                "title": "Implement deployment audit trail",
                "requirement_markdown": "Add deployment event tracking to the operations console backend.",
                "acceptance_criteria": "Deploy events are captured, queryable, and visible in the UI.",
                "implementation_steps": "Create schema, write API endpoints, and connect event views.",
                "status": TaskStatus.IN_PROGRESS,
                "assigned_engineer_index": 0,
                "branch_name": "feature/deploy-audit-trail",
                "pr_url": "https://github.com/acme/orion-devops-console/pull/18",
            },
            {
                "title": "Validate environment switcher UX",
                "requirement_markdown": "Test the environment switcher across desktop and tablet layouts.",
                "acceptance_criteria": "UX issues are documented with screenshots and recommended fixes.",
                "implementation_steps": "Run responsive checks and capture evidence.",
                "status": TaskStatus.AI_TESTING,
                "assigned_engineer_index": 2,
            },
            {
                "title": "Push metrics worker to dev",
                "requirement_markdown": "The metrics worker is approved and waiting for final deployment.",
                "acceptance_criteria": "Worker is merged, deployed to dev, and health checks are green.",
                "implementation_steps": "Merge approved PR and confirm worker health.",
                "status": TaskStatus.READY_TO_DEPLOY,
                "assigned_engineer_index": 3,
                "pr_url": "https://github.com/acme/orion-devops-console/pull/17",
            },
        ],
    },
]


def seed_engineers(session) -> None:
    if session.query(Engineer).count():
        return
    for engineer_data in DEFAULT_ENGINEERS:
        session.add(Engineer(**engineer_data))
    session.commit()


def seed_demo_workspace(session) -> None:
    engineers = session.query(Engineer).order_by(Engineer.id.asc()).all()
    if not engineers:
        return

    for project_data in DEMO_PROJECTS:
        project = session.query(Project).filter(Project.name == project_data["name"]).one_or_none()
        if project is None:
            project = Project(
                name=project_data["name"],
                repo_url=project_data["repo_url"],
                default_branch=project_data["default_branch"],
                deploy_config=project_data["deploy_config"],
                engineer_pool=[engineer.name for engineer in engineers],
            )
            session.add(project)
            session.flush()

        existing_task_count = session.query(Task).filter(Task.project_id == project.id).count()
        if existing_task_count:
            continue

        for task_data in project_data["tasks"]:
            assigned_engineer = engineers[task_data["assigned_engineer_index"]]
            payload = {
                key: value
                for key, value in task_data.items()
                if key != "assigned_engineer_index"
            }
            session.add(Task(project_id=project.id, assigned_engineer_id=assigned_engineer.id, **payload))

    session.commit()
