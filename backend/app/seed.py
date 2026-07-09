from app.enums import EngineerTemplate, MembershipRole, ModelProvider, TaskStatus
from app.models import (
    Engineer,
    Organization,
    OrganizationMember,
    Project,
    Tag,
    Task,
    User,
    Workflow,
    WorkflowStage,
)


DEFAULT_ORG = {"name": "Dev Boss Workspace", "slug": "devboss"}

DEMO_TAGS = [
    {"name": "Sprint 1", "color": "#3b82f6"},
    {"name": "Sprint 2", "color": "#8b5cf6"},
    {"name": "Bug", "color": "#ef4444"},
    {"name": "Feature", "color": "#22c55e"},
    {"name": "Tech Debt", "color": "#f59e0b"},
]


DEFAULT_ENGINEERS = [
    {
        "name": "Backend Engineer",
        "template": EngineerTemplate.BACKEND,
        "model_provider": ModelProvider.DEEPSEEK,
        "skill_markdown": "# Backend Engineer\n\nOwns API, schema, integrations, and tests.",
    },
    {
        "name": "Frontend Engineer",
        "template": EngineerTemplate.FRONTEND,
        "model_provider": ModelProvider.DEEPSEEK,
        "skill_markdown": "# Frontend Engineer\n\nOwns dashboard UX, React, and state management.",
    },
    {
        "name": "QA/Test Engineer",
        "template": EngineerTemplate.QA,
        "model_provider": ModelProvider.DEEPSEEK,
        "skill_markdown": "# QA/Test Engineer\n\nOwns verification plans and evidence capture.",
    },
    {
        "name": "DevOps/Deployment Engineer",
        "template": EngineerTemplate.DEVOPS,
        "model_provider": ModelProvider.DEEPSEEK,
        "skill_markdown": "# DevOps/Deployment Engineer\n\nOwns deploy scripts, health checks, and runtime ops.",
    },
]

DEFAULT_WORKFLOW = {
    "name": "Standard SDLC Pipeline",
    "description": "Default software delivery pipeline: Plan → Build → Test → Deploy",
    "stages": [
        {
            "name": "AI Grooming",
            "stage_order": 0,
            "is_ai_executable": True,
            "requires_human_approval": False,
            "stage_instructions": (
                "You are in the AI Grooming stage. Your job is to analyze the task requirements and the repository "
                "to identify missing information, risks, and ambiguities. Do NOT implement anything.\n\n"
                "Outcome JSON keys:\n"
                "- outcome_type: \"completed\" | \"needs_human_input\" | \"blocked\" | \"failed\"\n"
                "- summary: explanation of findings\n\n"
                "Reply with only a single JSON object and no markdown fences."
            ),
        },
        {
            "name": "Approval Gate",
            "stage_order": 1,
            "is_ai_executable": False,
            "requires_human_approval": True,
            "stage_instructions": None,
        },
        {
            "name": "Build",
            "stage_order": 2,
            "is_ai_executable": True,
            "requires_human_approval": False,
            "max_rework_attempts": 3,
            "rework_target_stage_id": None,
            "stage_instructions": (
                "You are in the Build stage. Implement the task requirements end-to-end. "
                "Add or update tests, run local verification, commit your changes, and push the branch.\n\n"
                "Do NOT create or link a pull request.\n\n"
                "Outcome JSON keys:\n"
                "- outcome_type: \"completed\" | \"needs_human_input\" | \"blocked\" | \"failed\"\n"
                "- summary: explanation of what was done\n"
                "- branch_name: the git branch you worked on\n\n"
                "Reply with only a single JSON object and no markdown fences."
            ),
        },
        {
            "name": "QA Testing",
            "stage_order": 3,
            "is_ai_executable": True,
            "requires_human_approval": False,
            "max_rework_attempts": 2,
            "rework_target_stage_id": None,
            "stage_instructions": (
                "You are in the QA Testing stage. Inspect the code and test coverage on the implementation branch. "
                "Run the strongest available verification. Look for regressions, edge cases, and quality issues.\n\n"
                "Do NOT do broad new feature work — only verify the existing implementation.\n\n"
                "Outcome JSON keys:\n"
                "- outcome_type: \"completed\" | \"needs_human_input\" | \"blocked\" | \"failed\"\n"
                "- summary: testing results and findings\n\n"
                "Reply with only a single JSON object and no markdown fences."
            ),
        },
        {
            "name": "Deploy",
            "stage_order": 4,
            "is_ai_executable": True,
            "requires_human_approval": True,
            "max_rework_attempts": 2,
            "rework_target_stage_id": None,
            "stage_instructions": (
                "You are in the Deploy stage. Deploy the task from the default branch using the project's "
                "deployment configuration. Use AWS CLI if required. Capture deployment evidence (URLs, invalidation IDs).\n\n"
                "Outcome JSON keys:\n"
                "- outcome_type: \"completed\" | \"needs_human_input\" | \"blocked\" | \"failed\"\n"
                "- summary: deployment results\n"
                "- deploy_url: the live deployment URL\n"
                "- pr_url: pull request URL if one was created\n\n"
                "Reply with only a single JSON object and no markdown fences."
            ),
        },
    ],
}

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


def seed_workflow(session, engineers: list[Engineer]) -> Workflow | None:
    existing = session.query(Workflow).filter(Workflow.name == DEFAULT_WORKFLOW["name"]).first()
    if existing:
        return existing

    workflow = Workflow(name=DEFAULT_WORKFLOW["name"], description=DEFAULT_WORKFLOW["description"])
    session.add(workflow)
    session.flush()

    for idx, stage_data in enumerate(DEFAULT_WORKFLOW["stages"]):
        if idx == 0:
            stage_data["assigned_engineer_id"] = engineers[0].id if len(engineers) > 0 else None
        elif idx == 2:
            stage_data["assigned_engineer_id"] = engineers[0].id if len(engineers) > 0 else None
            stage_data["rework_target_stage_id"] = None
        elif idx == 3:
            stage_data["assigned_engineer_id"] = engineers[2].id if len(engineers) > 2 else None
            stage_data["rework_target_stage_id"] = None
        elif idx == 4:
            stage_data["assigned_engineer_id"] = engineers[3].id if len(engineers) > 3 else None
            stage_data["rework_target_stage_id"] = None

        stage = WorkflowStage(workflow_id=workflow.id, **{k: v for k, v in stage_data.items() if k != "rework_target_stage_id"})
        session.add(stage)

    session.flush()

    stages = session.query(WorkflowStage).filter(WorkflowStage.workflow_id == workflow.id).order_by(WorkflowStage.stage_order).all()
    if len(stages) >= 4:
        stages[2].rework_target_stage_id = stages[2].id
        stages[3].rework_target_stage_id = stages[2].id
        stages[4].rework_target_stage_id = stages[4].id

    session.commit()
    return workflow


def seed_organization(session) -> Organization | None:
    existing = session.query(Organization).filter(Organization.slug == DEFAULT_ORG["slug"]).first()
    if existing:
        return existing
    org = Organization(name=DEFAULT_ORG["name"], slug=DEFAULT_ORG["slug"])
    session.add(org)
    session.flush()

    admin_email = "admin@devboss.local"
    user = session.query(User).filter(User.email == admin_email).first()
    if not user:
        user = User(email=admin_email, name="Admin User")
        session.add(user)
        session.flush()

    member = OrganizationMember(organization_id=org.id, user_id=user.id, role=MembershipRole.ADMIN)
    session.add(member)

    for tag_data in DEMO_TAGS:
        existing_tag = session.query(Tag).filter(Tag.organization_id == org.id, Tag.name == tag_data["name"]).first()
        if not existing_tag:
            session.add(Tag(organization_id=org.id, name=tag_data["name"], color=tag_data["color"]))

    session.commit()
    return org


def seed_demo_workspace(session) -> None:
    engineers = session.query(Engineer).order_by(Engineer.id.asc()).all()
    if not engineers:
        return

    org = seed_organization(session)
    workflow = seed_workflow(session, engineers)
    stages = session.query(WorkflowStage).filter(WorkflowStage.workflow_id == workflow.id).order_by(WorkflowStage.stage_order).all() if workflow else []

    for project_data in DEMO_PROJECTS:
        project = session.query(Project).filter(Project.name == project_data["name"]).one_or_none()
        if project is None:
            project = Project(
                name=project_data["name"],
                repo_url=project_data["repo_url"],
                default_branch=project_data["default_branch"],
                deploy_config=project_data["deploy_config"],
                engineer_pool=[engineer.name for engineer in engineers],
                workflow_id=workflow.id if workflow else None,
                organization_id=org.id if org else None,
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
            workflow_stage_id = None
            if stages and task_data["status"] == TaskStatus.AI_GROOMING:
                workflow_stage_id = stages[0].id if len(stages) > 0 else None
            elif stages and task_data["status"] == TaskStatus.IN_PROGRESS:
                workflow_stage_id = stages[2].id if len(stages) > 2 else None
            elif stages and task_data["status"] == TaskStatus.AI_TESTING:
                workflow_stage_id = stages[3].id if len(stages) > 3 else None

            session.add(Task(
                project_id=project.id,
                assigned_engineer_id=assigned_engineer.id,
                workflow_stage_id=workflow_stage_id,
                **payload,
            ))

    session.commit()
