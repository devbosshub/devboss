from pathlib import Path

from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.enums import ArtifactKind, CommentAuthorType, EngineerRuntimeStatus, OutcomeType, RunPhase, RunStatus, TaskStatus
from app.models import ConfigSetting, Engineer, EvidenceArtifact, Project, Task, TaskComment, TaskRun
from app.schemas import AgentOutcome, TaskCommentCreate, TaskCreate, TaskUpdate
from app.storage import LocalArtifactStorage
from app.workflow import (
    OUTCOME_TO_STATUS,
    can_transition,
    execution_status_for_phase,
    is_allowed_outcome_for_status,
    required_phase_for_status,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


MAX_TESTING_REWORK_LOOPS = 3


PROMPT_DIRECTORY = Path(__file__).resolve().parent / "prompts"
STAGE_PROMPT_FILES = {
    TaskStatus.AI_GROOMING: "ai_grooming.md",
    TaskStatus.IN_PROGRESS: "in_progress.md",
    TaskStatus.AI_TESTING: "ai_testing.md",
    TaskStatus.READY_TO_DEPLOY: "ready_to_deploy.md",
    TaskStatus.DEPLOYED: "deployment.md",
}


def load_stage_instructions(task_status: TaskStatus) -> str:
    file_name = STAGE_PROMPT_FILES.get(task_status)
    if not file_name:
        return ""
    prompt_path = PROMPT_DIRECTORY / file_name
    if not prompt_path.exists():
        raise HTTPException(status_code=500, detail=f"Missing stage prompt file for status '{task_status.value}'")
    return prompt_path.read_text(encoding="utf-8").strip()


def get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def delete_project(db: Session, project_id: int) -> None:
    project = get_project_or_404(db, project_id)
    db.delete(project)
    db.commit()


def get_engineer_or_404(db: Session, engineer_id: int) -> Engineer:
    engineer = db.get(Engineer, engineer_id)
    if not engineer:
        raise HTTPException(status_code=404, detail="Engineer not found")
    return engineer


def delete_engineer(db: Session, engineer_id: int) -> Engineer:
    engineer = get_engineer_or_404(db, engineer_id)
    has_assigned_tasks = db.scalar(select(Task.id).where(Task.assigned_engineer_id == engineer.id).limit(1))
    if has_assigned_tasks:
        raise HTTPException(status_code=400, detail="Cannot delete engineer while tasks are still assigned.")

    has_task_runs = db.scalar(select(TaskRun.id).where(TaskRun.engineer_id == engineer.id).limit(1))
    if has_task_runs:
        raise HTTPException(status_code=400, detail="Cannot delete engineer with historical task runs.")

    db.delete(engineer)
    db.commit()
    return engineer


def refresh_engineer_runtime_health(db: Session, engineer: Engineer, heartbeat_timeout_seconds: int) -> Engineer:
    is_running_like = engineer.runtime_status in {
        EngineerRuntimeStatus.STARTING,
        EngineerRuntimeStatus.HEALTHY,
        EngineerRuntimeStatus.HEARTBEAT_MISSING,
    }
    if not is_running_like:
        return engineer

    reference_time = engineer.runtime_last_heartbeat_at or engineer.runtime_started_at
    if reference_time is None:
        return engineer
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)

    heartbeat_age = (utcnow() - reference_time).total_seconds()
    next_status = (
        EngineerRuntimeStatus.HEALTHY
        if heartbeat_age <= heartbeat_timeout_seconds
        else EngineerRuntimeStatus.HEARTBEAT_MISSING
    )
    if engineer.runtime_status != next_status:
        engineer.runtime_status = next_status
        engineer.runtime_status_message = (
            "Runtime heartbeat is current."
            if next_status == EngineerRuntimeStatus.HEALTHY
            else "Heartbeat missing. Runtime may be down."
        )
        engineer.updated_at = utcnow()
        db.add(engineer)
        db.commit()
        db.refresh(engineer)
    return engineer


def list_engineers_with_runtime_health(db: Session, heartbeat_timeout_seconds: int) -> list[Engineer]:
    engineers = list(db.scalars(select(Engineer).order_by(Engineer.created_at.asc())))
    return [refresh_engineer_runtime_health(db, engineer, heartbeat_timeout_seconds) for engineer in engineers]


def get_task_or_404(db: Session, task_id: int) -> Task:
    stmt = (
        select(Task)
        .options(
            selectinload(Task.comments),
            selectinload(Task.task_runs),
            selectinload(Task.artifacts),
        )
        .where(Task.id == task_id)
    )
    task = db.scalar(stmt)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def get_comment_or_404(db: Session, task_id: int, comment_id: int) -> TaskComment:
    comment = db.get(TaskComment, comment_id)
    if not comment or comment.task_id != task_id:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


def list_tasks_by_status(db: Session, project_id: int | None = None) -> list[Task]:
    stmt = (
        select(Task)
        .options(
            selectinload(Task.comments),
            selectinload(Task.task_runs),
            selectinload(Task.artifacts),
        )
        .order_by(Task.updated_at.desc())
    )
    if project_id is not None:
        stmt = stmt.where(Task.project_id == project_id)
    return list(db.scalars(stmt))


def list_attention_tasks(db: Session) -> list[Task]:
    tasks = list_tasks_by_status(db)
    attention_statuses = {
        TaskStatus.READY_FOR_BUILD,
        TaskStatus.HUMAN_TESTING,
        TaskStatus.READY_TO_DEPLOY,
    }
    return [
        task
        for task in tasks
        if task.blocked_reason
        or any(comment.action_required for comment in task.comments)
        or task.status in attention_statuses
    ]


def create_task(db: Session, payload: TaskCreate) -> Task:
    get_project_or_404(db, payload.project_id)
    if payload.assigned_engineer_id is not None:
        get_engineer_or_404(db, payload.assigned_engineer_id)
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return get_task_or_404(db, task.id)


def update_task(db: Session, task_id: int, payload: TaskUpdate) -> Task:
    task = get_task_or_404(db, task_id)
    updates = payload.model_dump(exclude_unset=True)
    target_status = updates.get("status")
    if target_status and target_status != task.status:
        if not can_transition(task.status, target_status):
            raise HTTPException(status_code=400, detail=f"Invalid status transition from {task.status} to {target_status}")
        task.status = target_status
        maybe_create_task_run(db, task)
        updates.pop("status")
    for field, value in updates.items():
        setattr(task, field, value)
    task.updated_at = utcnow()
    db.add(task)
    db.commit()
    db.refresh(task)
    return get_task_or_404(db, task.id)


def add_comment(db: Session, task_id: int, payload: TaskCommentCreate) -> TaskComment:
    task = get_task_or_404(db, task_id)
    comment = TaskComment(task_id=task.id, **payload.model_dump())
    db.add(comment)
    if task.task_runs and payload.author_type == CommentAuthorType.HUMAN:
        latest_run = sorted(task.task_runs, key=lambda run: run.created_at)[-1]
        if latest_run.status == RunStatus.WAITING_HUMAN:
            latest_run.status = RunStatus.PENDING
            latest_run.summary = "Human replied, re-queued for engineer execution."
            latest_run.heartbeat_at = utcnow()
            latest_run.updated_at = utcnow()
            db.add(latest_run)
    db.commit()
    db.refresh(comment)
    return comment


def maybe_create_task_run(db: Session, task: Task) -> Task | None:
    phase = required_phase_for_status(task.status)
    if phase is None or task.assigned_engineer_id is None:
        return None
    open_run = db.scalar(
        select(TaskRun).where(
            TaskRun.task_id == task.id,
            TaskRun.phase == phase,
            TaskRun.status.in_([RunStatus.PENDING, RunStatus.CLAIMED, RunStatus.RUNNING, RunStatus.WAITING_HUMAN]),
        )
    )
    if open_run:
        return task
    run = TaskRun(task_id=task.id, engineer_id=task.assigned_engineer_id, phase=phase, status=RunStatus.PENDING)
    db.add(run)
    db.commit()
    return task


def approve_task_run(db: Session, task_run_id: int, summary: str | None = None) -> TaskRun:
    task_run = db.get(TaskRun, task_run_id)
    if not task_run:
        raise HTTPException(status_code=404, detail="Task run not found")
    task = get_task_or_404(db, task_run.task_id)
    if task.status == TaskStatus.AI_GROOMING:
        next_status = TaskStatus.READY_FOR_BUILD
    elif task.status == TaskStatus.READY_FOR_BUILD:
        next_status = TaskStatus.IN_PROGRESS
    elif task.status == TaskStatus.READY_TO_DEPLOY:
        next_status = TaskStatus.DEPLOYED
    else:
        raise HTTPException(status_code=400, detail="Approval is not available for this task status")
    if not can_transition(task.status, next_status):
        raise HTTPException(status_code=400, detail="Invalid approval transition")
    task.status = next_status
    task.blocked_reason = None
    task.updated_at = utcnow()
    if summary:
        task_run.summary = summary
    db.add(task)
    db.add(task_run)
    db.commit()
    maybe_create_task_run(db, task)
    refreshed = db.get(TaskRun, task_run_id)
    return refreshed


def reject_task_run(db: Session, task_run_id: int, summary: str | None = None) -> TaskRun:
    task_run = db.get(TaskRun, task_run_id)
    if not task_run:
        raise HTTPException(status_code=404, detail="Task run not found")
    task_run.status = RunStatus.REJECTED
    task_run.summary = summary or "Rejected by human"
    task_run.updated_at = utcnow()
    db.add(task_run)
    db.commit()
    db.refresh(task_run)
    return task_run


def latest_task_run_for_task(task: Task) -> TaskRun | None:
    if not task.task_runs:
        return None
    return sorted(task.task_runs, key=lambda run: run.created_at)[-1]


def retry_task(db: Session, task_id: int) -> Task:
    task = get_task_or_404(db, task_id)
    if task.assigned_engineer_id is None:
        raise HTTPException(status_code=400, detail="Assign an engineer before retrying this task")

    target_phase = required_phase_for_status(task.status)
    if target_phase is None:
        latest_run = latest_task_run_for_task(task)
        if latest_run is None:
            raise HTTPException(status_code=400, detail="This task does not have a runnable stage to retry")
        target_phase = latest_run.phase
        task.status = execution_status_for_phase(target_phase)

    open_run = db.scalar(
        select(TaskRun).where(
            TaskRun.task_id == task.id,
            TaskRun.phase == target_phase,
            TaskRun.status.in_([RunStatus.PENDING, RunStatus.CLAIMED, RunStatus.RUNNING, RunStatus.WAITING_HUMAN]),
        )
    )

    if open_run:
        open_run.status = RunStatus.PENDING
        open_run.summary = "Re-queued by human."
        open_run.outcome_type = None
        open_run.outcome_payload_json = None
        open_run.claimed_at = None
        open_run.started_at = None
        open_run.completed_at = None
        open_run.heartbeat_at = utcnow()
        open_run.updated_at = utcnow()
        db.add(open_run)
    else:
        db.add(TaskRun(task_id=task.id, engineer_id=task.assigned_engineer_id, phase=target_phase, status=RunStatus.PENDING))

    task.blocked_reason = None
    task.updated_at = utcnow()
    db.add(task)
    db.commit()
    return get_task_or_404(db, task.id)


def poll_next_task(db: Session, engineer_id: int) -> tuple[TaskRun | None, Task | None]:
    get_engineer_or_404(db, engineer_id)
    stmt = (
        select(TaskRun)
        .join(Task)
        .where(
            TaskRun.engineer_id == engineer_id,
            TaskRun.status == RunStatus.PENDING,
            Task.status.in_(
                [
                    TaskStatus.AI_GROOMING,
                    TaskStatus.IN_PROGRESS,
                    TaskStatus.AI_TESTING,
                    TaskStatus.READY_TO_DEPLOY,
                    TaskStatus.DEPLOYED,
                ]
            ),
        )
        .order_by(TaskRun.created_at.asc())
    )
    task_run = db.scalar(stmt)
    if not task_run:
        return None, None
    task_run.status = RunStatus.CLAIMED
    task_run.claimed_at = utcnow()
    task_run.started_at = utcnow()
    task_run.heartbeat_at = utcnow()
    db.add(task_run)
    db.commit()
    task = get_task_or_404(db, task_run.task_id)
    if task.blocked_reason:
        task.blocked_reason = None
        task.updated_at = utcnow()
        db.add(task)
        db.commit()
        task = get_task_or_404(db, task_run.task_id)
    return task_run, task


def update_heartbeat(db: Session, task_run_id: int, status_value: RunStatus | None, summary: str | None) -> TaskRun:
    task_run = db.get(TaskRun, task_run_id)
    if not task_run:
        raise HTTPException(status_code=404, detail="Task run not found")
    task_run.heartbeat_at = utcnow()
    if status_value is not None:
        task_run.status = status_value
    if summary:
        task_run.summary = summary
    db.add(task_run)
    db.commit()
    db.refresh(task_run)
    return task_run


def add_agent_log(db: Session, task_run_id: int, body: str, author_name: str, action_required: bool) -> TaskComment:
    task_run = db.get(TaskRun, task_run_id)
    if not task_run:
        raise HTTPException(status_code=404, detail="Task run not found")
    comment = TaskComment(
        task_id=task_run.task_id,
        author_type=CommentAuthorType.AGENT,
        author_name=author_name,
        body=body,
        action_required=action_required,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def add_task_comment(
    db: Session,
    task_id: int,
    author_type: CommentAuthorType,
    author_name: str,
    body: str,
    action_required: bool,
) -> TaskComment:
    comment = TaskComment(
        task_id=task_id,
        author_type=author_type,
        author_name=author_name,
        body=body,
        action_required=action_required,
    )
    db.add(comment)
    db.flush()
    return comment


def delete_comment(db: Session, task_id: int, comment_id: int) -> None:
    comment = get_comment_or_404(db, task_id, comment_id)
    db.delete(comment)
    db.commit()


def delete_task(db: Session, task_id: int) -> None:
    task = get_task_or_404(db, task_id)
    db.delete(task)
    db.commit()


def apply_agent_outcome(db: Session, task_run_id: int, payload: AgentOutcome) -> TaskRun:
    task_run = db.get(TaskRun, task_run_id)
    if not task_run:
        raise HTTPException(status_code=404, detail="Task run not found")
    task = get_task_or_404(db, task_run.task_id)
    if not is_allowed_outcome_for_status(task.status, payload.outcome_type):
        allowed = sorted(
            outcome.value
            for outcome in OUTCOME_TO_STATUS
            if is_allowed_outcome_for_status(task.status, outcome)
        )
        raise HTTPException(
            status_code=400,
            detail=(
                f"Outcome '{payload.outcome_type.value}' is not valid for task status '{task.status.value}'. "
                f"Allowed outcomes: {', '.join(allowed)}"
            ),
        )
    task_run.outcome_type = payload.outcome_type
    task_run.summary = payload.summary
    task_run.outcome_payload_json = payload.model_dump(mode="json")
    task_run.heartbeat_at = utcnow()

    if payload.branch_name and task.status != TaskStatus.AI_GROOMING:
        task.branch_name = payload.branch_name
    if payload.pr_url:
        task.pr_url = payload.pr_url
    if payload.deploy_url:
        task.deploy_url = payload.deploy_url
    if payload.blocked_reason:
        task.blocked_reason = payload.blocked_reason
    elif payload.outcome_type not in {OutcomeType.BLOCKED, OutcomeType.FAILED}:
        task.blocked_reason = None

    if task.status == TaskStatus.AI_TESTING and payload.outcome_type in {OutcomeType.BLOCKED, OutcomeType.FAILED}:
        loop_number = task.testing_rework_count + 1
        if task.testing_rework_count < MAX_TESTING_REWORK_LOOPS:
            task.testing_rework_count = loop_number
            task.status = TaskStatus.IN_PROGRESS
            task.updated_at = utcnow()
            task_run.status = RunStatus.COMPLETED
            task_run.completed_at = utcnow()
            task_run.summary = payload.summary
            add_task_comment(
                db,
                task.id,
                CommentAuthorType.AGENT,
                "ai-testing",
                "\n".join(
                    [
                        "## AI Testing Feedback",
                        "",
                        f"AI testing found issues that need code changes. Sending the task back to **In Progress** for another implementation pass.",
                        "",
                        f"**Loop:** {loop_number} of {MAX_TESTING_REWORK_LOOPS}",
                        "",
                        "### Summary",
                        "",
                        payload.summary,
                        "",
                        "### Fix Guidance",
                        "",
                        payload.blocked_reason or "Review the latest testing findings and address the failing behavior before running AI testing again.",
                    ]
                ),
                action_required=False,
            )
            db.add(task)
            db.add(task_run)
            db.commit()
            maybe_create_task_run(db, task)
            db.refresh(task_run)
            return task_run

        task_run.status = RunStatus.WAITING_HUMAN
        task_run.summary = payload.summary
        task.blocked_reason = payload.blocked_reason or payload.summary
        add_task_comment(
            db,
            task.id,
            CommentAuthorType.AGENT,
            "ai-testing",
            "\n".join(
                [
                    "## Human Input Needed",
                    "",
                    f"AI testing has already sent this task back for fixes **{MAX_TESTING_REWORK_LOOPS} times**.",
                    "The task is now paused for human review before another attempt.",
                    "",
                    "### Latest Testing Summary",
                    "",
                    payload.summary,
                    "",
                    "### Reason For Pause",
                    "",
                    payload.blocked_reason or "Too many automated implementation-testing loops without a passing result.",
                    "",
                    "Please review the task thread and reply with guidance before retrying the task.",
                ]
            ),
            action_required=True,
        )
        db.add(task)
        db.add(task_run)
        db.commit()
        db.refresh(task_run)
        return task_run

    if payload.outcome_type == OutcomeType.DEPLOYMENT_COMPLETE:
        if task.status == TaskStatus.READY_TO_DEPLOY:
            next_status = None
        elif task.status == TaskStatus.DEPLOYED:
            next_status = TaskStatus.ARCHIVED
        else:
            next_status = OUTCOME_TO_STATUS[payload.outcome_type]
    else:
        next_status = OUTCOME_TO_STATUS[payload.outcome_type]
    if payload.outcome_type == OutcomeType.NEEDS_HUMAN_INPUT:
        task_run.status = RunStatus.WAITING_HUMAN
    elif payload.outcome_type in {OutcomeType.BLOCKED, OutcomeType.FAILED}:
        task_run.status = RunStatus.FAILED
    else:
        task_run.status = RunStatus.COMPLETED
        task_run.completed_at = utcnow()

    if next_status:
        if not can_transition(task.status, next_status):
            raise HTTPException(status_code=400, detail=f"Invalid outcome transition from {task.status} to {next_status}")
        task.status = next_status
        if payload.outcome_type == OutcomeType.TESTING_COMPLETE:
            task.testing_rework_count = 0
        task.updated_at = utcnow()
        db.add(task)
        db.add(task_run)
        db.commit()
        maybe_create_task_run(db, task)
    else:
        db.add(task)
        db.add(task_run)
        db.commit()

    db.refresh(task_run)
    return task_run


def store_artifact(
    db: Session,
    storage: LocalArtifactStorage,
    task_id: int,
    task_run_id: int | None,
    kind: ArtifactKind,
    upload: UploadFile,
) -> EvidenceArtifact:
    get_task_or_404(db, task_id)
    path, content_type = storage.save_upload(task_id, upload)
    artifact = EvidenceArtifact(
        task_id=task_id,
        task_run_id=task_run_id,
        kind=kind,
        name=upload.filename or "artifact",
        file_path=path,
        content_type=content_type,
        metadata_json={},
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


def build_task_bundle(task: Task, project: Project, engineer: Engineer) -> dict:
    open_questions = [comment.body for comment in task.comments if comment.action_required]
    bundle = {
        "TASK.md": "\n".join(
            [
                f"# {task.title}",
                "",
                f"Status: {task.status.value}",
                "",
                "## Requirements",
                task.requirement_markdown,
                "",
                "## Acceptance Criteria",
                task.acceptance_criteria,
                "",
                "## Implementation Steps",
                task.implementation_steps or "_Not provided_",
                "",
                "## Open Questions",
                "\n".join(f"- {question}" for question in open_questions) or "- None",
            ]
        ),
        "COMMENTS.md": "\n\n".join(
            [f"## {comment.author_name} ({comment.author_type.value})\n{comment.body}" for comment in task.comments]
        ),
        "PROJECT_CONTEXT.md": "\n".join(
            [
                f"# Project: {project.name}",
                "",
                f"Repository: {project.repo_url}",
                f"Default Branch: {project.default_branch}",
                f"Task Branch: {task.branch_name or '_Not created yet_'}",
                "",
                "## Deploy Config",
                str(project.deploy_config),
                "",
                "## Deployment Instructions",
                project.deployment_instructions or "_Not provided_",
                "",
                f"## Engineer",
                engineer.name,
                "",
                engineer.skill_markdown,
            ]
        ),
        "ATTACHMENTS": [artifact.file_path for artifact in task.artifacts],
    }
    stage_instructions = load_stage_instructions(task.status)
    if stage_instructions:
        bundle["STAGE_INSTRUCTIONS.md"] = stage_instructions
    return bundle


def list_config_settings(db: Session) -> list[ConfigSetting]:
    return list(db.scalars(select(ConfigSetting).order_by(ConfigSetting.key.asc())))


def get_config_setting_by_key(db: Session, key: str) -> ConfigSetting:
    setting = db.scalar(select(ConfigSetting).where(ConfigSetting.key == key))
    if not setting:
        raise HTTPException(status_code=404, detail=f"Config setting '{key}' not found")
    return setting


def get_optional_config_setting_by_key(db: Session, key: str) -> ConfigSetting | None:
    return db.scalar(select(ConfigSetting).where(ConfigSetting.key == key))


def create_config_setting(
    db: Session,
    key: str,
    value: str,
    is_secret: bool,
    description: str | None,
) -> ConfigSetting:
    existing = db.scalar(select(ConfigSetting).where(ConfigSetting.key == key))
    if existing:
        raise HTTPException(status_code=400, detail="Config key already exists")
    setting = ConfigSetting(key=key, value=value, is_secret=is_secret, description=description)
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


def update_config_setting(
    db: Session,
    setting_id: int,
    value: str | None,
    is_secret: bool | None,
    description: str | None,
) -> ConfigSetting:
    setting = db.get(ConfigSetting, setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail="Config setting not found")
    if value is not None:
        setting.value = value
    if is_secret is not None:
        setting.is_secret = is_secret
    if description is not None:
        setting.description = description
    setting.updated_at = utcnow()
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


def delete_config_setting(db: Session, setting_id: int) -> None:
    setting = db.get(ConfigSetting, setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail="Config setting not found")
    db.delete(setting)
    db.commit()


def mark_engineer_runtime_launching(db: Session, engineer: Engineer, container_name: str, container_id: str) -> Engineer:
    engineer.runtime_status = EngineerRuntimeStatus.STARTING
    engineer.runtime_container_name = container_name
    engineer.runtime_container_id = container_id
    engineer.runtime_status_message = "Container launched. Waiting for heartbeat."
    engineer.runtime_started_at = utcnow()
    engineer.runtime_last_heartbeat_at = None
    engineer.updated_at = utcnow()
    db.add(engineer)
    db.commit()
    db.refresh(engineer)
    return engineer


def mark_engineer_runtime_stopped(db: Session, engineer: Engineer, message: str = "Runtime stopped.") -> Engineer:
    engineer.runtime_status = EngineerRuntimeStatus.STOPPED
    engineer.runtime_status_message = message
    engineer.runtime_container_name = None
    engineer.runtime_container_id = None
    engineer.runtime_started_at = None
    engineer.runtime_last_heartbeat_at = None
    engineer.updated_at = utcnow()
    db.add(engineer)
    db.commit()
    db.refresh(engineer)
    return engineer


def record_engineer_heartbeat(
    db: Session,
    engineer_id: int,
    container_name: str,
    container_id: str | None,
    status_message: str | None,
) -> Engineer:
    engineer = get_engineer_or_404(db, engineer_id)
    engineer.runtime_status = EngineerRuntimeStatus.HEALTHY
    engineer.runtime_container_name = container_name
    engineer.runtime_container_id = container_id or engineer.runtime_container_id
    engineer.runtime_status_message = status_message or "Runtime heartbeat received."
    if engineer.runtime_started_at is None:
        engineer.runtime_started_at = utcnow()
    engineer.runtime_last_heartbeat_at = utcnow()
    engineer.updated_at = utcnow()
    db.add(engineer)
    db.commit()
    db.refresh(engineer)
    return engineer
