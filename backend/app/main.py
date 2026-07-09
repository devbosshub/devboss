from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.database import Base, engine, get_db
from app.enums import ArtifactKind, CommentAuthorType, EngineerRuntimeStatus, MembershipRole, ModelProvider, PRDStatus, RunStatus, StatusGroup, TaskStatus, PROVIDER_ENV_VAR_MAP
from app.models import ConfigSetting, Engineer, EngineerRuntime, Organization, OrganizationMember, PRD, PRDComment, Project, Tag, Task, TaskRun, TokenUsage, User, Workflow, WorkflowStage
from app.schemas import (
    AgentHeartbeat,
    AgentLog,
    AgentOutcome,
    AgentPollRequest,
    AgentPollResponse,
    BoardLane,
    BoardRead,
    ConfigSettingCreate,
    ConfigSettingRead,
    ConfigSettingUpdate,
    EngineerCreate,
    EngineerHeartbeat,
    EngineerRead,
    EngineerRuntimeRead,
    EngineerUpdate,
    OrgMemberCreate,
    OrganizationCreate,
    OrganizationMemberRead,
    OrganizationRead,
    OrganizationUpdate,
    PRDCommentCreate,
    PRDCommentRead,
    PRDChatMessage,
    PRDConvertRequest,
    PRDCreate,
    PRDRead,
    PRDUpdate,
    PRDTagsUpdate,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    StageReorderRequest,
    TagCreate,
    TagRead,
    TaskCommentCreate,
    TaskCommentRead,
    TaskCreate,
    TaskRead,
    TaskRunApprovalRequest,
    TaskRunRead,
    TaskUpdate,
    TaskTagsUpdate,
    TokenSummary,
    TokenUsageCreate,
    TokenUsageRead,
    UserRead,
    WorkflowCreate,
    WorkflowRead,
    WorkflowStageCreate,
    WorkflowStageRead,
    WorkflowStageUpdate,
    WorkflowUpdate,
)
from app.runtime_manager import DockerRuntimeManager
from app.seed import seed_demo_workspace, seed_engineers
from app.services import (
    add_agent_log,
    add_comment,
    add_org_member,
    add_prd_comment,
    apply_agent_outcome,
    approve_task_run,
    archive_organization as delete_organization_svc,
    convert_prd_to_tasks,
    create_config_setting,
    create_engineer_runtime,
    create_organization,
    create_prd,
    create_tag as create_tag_svc,
    create_task,
    create_workflow_stage,
    delete_comment,
    delete_engineer,
    delete_project,
    delete_tag as delete_tag_svc,
    delete_task,
    delete_workflow_stage,
    build_task_bundle,
    find_reusable_engineer_runtime,
    get_config_setting_by_key,
    get_engineer_or_404,
    get_engineer_runtime_or_404,
    get_optional_config_setting_by_key,
    get_organization_or_404,
    get_or_create_user,
    get_prd_or_404,
    get_project_or_404,
    get_project_token_summary,
    get_tag_or_404,
    get_task_or_404,
    get_task_token_summary,
    get_workflow_or_404,
    get_workflow_stage_or_404,
    list_attention_tasks,
    list_config_settings,
    list_engineers_with_runtime_health,
    list_organizations,
    list_prds,
    list_tasks_by_status,
    list_workflows,
    mark_engineer_runtime_launching,
    mark_engineer_runtime_stopped,
    maybe_create_task_run,
    poll_next_task,
    record_engineer_runtime_heartbeat,
    record_token_usage,
    refresh_engineer_runtime_health,
    reject_task_run,
    remove_org_member,
    reorder_workflow_stages,
    retry_task,
    set_prd_tags,
    set_task_tags,
    store_artifact,
    update_config_setting,
    update_heartbeat,
    update_org_member_role,
    update_prd,
    update_task,
    update_workflow_stage,
)
from app.storage import LocalArtifactStorage


settings = get_settings()
storage = LocalArtifactStorage()
runtime_manager = DockerRuntimeManager(settings)


def ensure_runtime_schema() -> None:
    inspector = inspect(engine)
    engineer_columns = {column["name"] for column in inspector.get_columns("engineers")}
    task_columns = {column["name"] for column in inspector.get_columns("tasks")}
    task_run_columns = {column["name"] for column in inspector.get_columns("task_runs")}
    project_columns = {column["name"] for column in inspector.get_columns("projects")}
    runtime_tables = set(inspector.get_table_names())
    runtime_columns = (
        {column["name"] for column in inspector.get_columns("engineer_runtimes")}
        if "engineer_runtimes" in runtime_tables
        else set()
    )
    timestamp_type = "TIMESTAMP" if engine.dialect.name == "sqlite" else "TIMESTAMP WITH TIME ZONE"
    statements: list[str] = []

    if "runtime_status" not in engineer_columns:
        statements.append("ALTER TABLE engineers ADD COLUMN runtime_status VARCHAR(64) DEFAULT 'stopped'")
    if "runtime_container_name" not in engineer_columns:
        statements.append("ALTER TABLE engineers ADD COLUMN runtime_container_name VARCHAR(255)")
    if "runtime_container_id" not in engineer_columns:
        statements.append("ALTER TABLE engineers ADD COLUMN runtime_container_id VARCHAR(255)")
    if "runtime_status_message" not in engineer_columns:
        statements.append("ALTER TABLE engineers ADD COLUMN runtime_status_message TEXT")
    if "runtime_started_at" not in engineer_columns:
        statements.append(f"ALTER TABLE engineers ADD COLUMN runtime_started_at {timestamp_type}")
    if "runtime_last_heartbeat_at" not in engineer_columns:
        statements.append(f"ALTER TABLE engineers ADD COLUMN runtime_last_heartbeat_at {timestamp_type}")
    if "deployment_instructions" not in project_columns:
        statements.append("ALTER TABLE projects ADD COLUMN deployment_instructions TEXT DEFAULT ''")
    if "testing_rework_count" not in task_columns:
        statements.append("ALTER TABLE tasks ADD COLUMN testing_rework_count INTEGER DEFAULT 0")
    if "release_queue_entered_at" not in task_columns:
        statements.append(f"ALTER TABLE tasks ADD COLUMN release_queue_entered_at {timestamp_type}")
    if "outcome_payload_json" not in task_run_columns:
        json_type = "TEXT" if engine.dialect.name == "sqlite" else "JSON"
        statements.append(f"ALTER TABLE task_runs ADD COLUMN outcome_payload_json {json_type}")
    if "claimed_by_runtime_id" not in task_run_columns:
        nullable_integer = "INTEGER"
        statements.append(f"ALTER TABLE task_runs ADD COLUMN claimed_by_runtime_id {nullable_integer}")
    if "model_provider" not in engineer_columns:
        statements.append("ALTER TABLE engineers ADD COLUMN model_provider VARCHAR(64) DEFAULT 'deepseek'")
    if "engineer_runtimes" in runtime_tables and "current_task_run_id" not in runtime_columns:
        statements.append("ALTER TABLE engineer_runtimes ADD COLUMN current_task_run_id INTEGER")
    if "workflow_id" not in project_columns:
        statements.append("ALTER TABLE projects ADD COLUMN workflow_id INTEGER")
    if "workflow_stage_id" not in task_columns:
        statements.append("ALTER TABLE tasks ADD COLUMN workflow_stage_id INTEGER")
    if "status_group" not in task_columns:
        statements.append("ALTER TABLE tasks ADD COLUMN status_group VARCHAR(64) DEFAULT 'todo'")
    if "rework_count" not in task_columns:
        statements.append("ALTER TABLE tasks ADD COLUMN rework_count INTEGER DEFAULT 0")
    if "workflow_stage_id" not in task_run_columns:
        statements.append("ALTER TABLE task_runs ADD COLUMN workflow_stage_id INTEGER")
    if "attempt_number" not in task_run_columns:
        statements.append("ALTER TABLE task_runs ADD COLUMN attempt_number INTEGER DEFAULT 1")
    if "organization_id" not in project_columns:
        statements.append("ALTER TABLE projects ADD COLUMN organization_id INTEGER")

    if statements:
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))

    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(text("ALTER TYPE runphase ADD VALUE IF NOT EXISTS 'READY_TO_DEPLOY'"))


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Path(settings.upload_path).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    ensure_runtime_schema()
    db = Session(bind=engine)
    try:
        seed_engineers(db)
        seed_demo_workspace(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Dev Boss API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/workflows", response_model=WorkflowRead)
def create_workflow(payload: WorkflowCreate, db: Session = Depends(get_db)) -> Workflow:
    workflow = Workflow(**payload.model_dump())
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return db.scalar(
        select(Workflow).options(selectinload(Workflow.stages)).where(Workflow.id == workflow.id)
    )


@app.get("/workflows", response_model=list[WorkflowRead])
def list_workflows_route(db: Session = Depends(get_db)) -> list[Workflow]:
    return list_workflows(db)


@app.get("/workflows/{workflow_id}", response_model=WorkflowRead)
def get_workflow(workflow_id: int, db: Session = Depends(get_db)) -> Workflow:
    return get_workflow_or_404(db, workflow_id)


@app.patch("/workflows/{workflow_id}", response_model=WorkflowRead)
def patch_workflow(workflow_id: int, payload: WorkflowUpdate, db: Session = Depends(get_db)) -> Workflow:
    workflow = get_workflow_or_404(db, workflow_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(workflow, field, value)
    workflow.updated_at = datetime.now()
    db.add(workflow)
    db.commit()
    return get_workflow_or_404(db, workflow_id)


@app.delete("/workflows/{workflow_id}")
def delete_workflow(workflow_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    workflow = get_workflow_or_404(db, workflow_id)
    db.delete(workflow)
    db.commit()
    return {"deleted": True}


@app.post("/workflows/{workflow_id}/stages", response_model=WorkflowStageRead)
def create_workflow_stage_route(
    workflow_id: int, payload: WorkflowStageCreate, db: Session = Depends(get_db)
) -> WorkflowStage:
    return create_workflow_stage(db, workflow_id, payload.model_dump())


@app.patch("/workflows/{workflow_id}/stages/{stage_id}", response_model=WorkflowStageRead)
def patch_workflow_stage(
    workflow_id: int, stage_id: int, payload: WorkflowStageUpdate, db: Session = Depends(get_db)
) -> WorkflowStage:
    stage = get_workflow_stage_or_404(db, stage_id)
    if stage.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Stage not found in this workflow")
    return update_workflow_stage(db, stage_id, payload.model_dump(exclude_unset=True))


@app.delete("/workflows/{workflow_id}/stages/{stage_id}")
def delete_workflow_stage_route(
    workflow_id: int, stage_id: int, db: Session = Depends(get_db)
) -> dict[str, bool]:
    stage = get_workflow_stage_or_404(db, stage_id)
    if stage.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Stage not found in this workflow")
    delete_workflow_stage(db, stage_id)
    return {"deleted": True}


@app.patch("/workflows/{workflow_id}/stages/reorder", response_model=list[WorkflowStageRead])
def reorder_workflow_stages_route(
    workflow_id: int, payload: StageReorderRequest, db: Session = Depends(get_db)
) -> list[WorkflowStage]:
    items = [item.model_dump() for item in payload.stages]
    return reorder_workflow_stages(db, workflow_id, items)


@app.post("/projects", response_model=ProjectRead)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@app.get("/projects", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    return list(db.scalars(select(Project).order_by(Project.updated_at.desc())))


@app.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)) -> Project:
    return get_project_or_404(db, project_id)


@app.patch("/projects/{project_id}", response_model=ProjectRead)
def patch_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)) -> Project:
    project = get_project_or_404(db, project_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@app.delete("/projects/{project_id}")
def delete_project_route(project_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    delete_project(db, project_id)
    return {"deleted": True}


@app.post("/settings", response_model=ConfigSettingRead)
def create_setting(payload: ConfigSettingCreate, db: Session = Depends(get_db)) -> ConfigSetting:
    return create_config_setting(db, payload.key, payload.value, payload.is_secret, payload.description)


@app.get("/settings", response_model=list[ConfigSettingRead])
def get_settings_route(db: Session = Depends(get_db)) -> list[ConfigSetting]:
    return list_config_settings(db)


@app.patch("/settings/{setting_id}", response_model=ConfigSettingRead)
def patch_setting(setting_id: int, payload: ConfigSettingUpdate, db: Session = Depends(get_db)) -> ConfigSetting:
    return update_config_setting(db, setting_id, payload.value, payload.is_secret, payload.description)


@app.delete("/settings/{setting_id}")
def delete_setting(setting_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    delete_config_setting(db, setting_id)
    return {"deleted": True}


@app.post("/engineers", response_model=EngineerRead)
def create_engineer(payload: EngineerCreate, db: Session = Depends(get_db)) -> Engineer:
    engineer = Engineer(**payload.model_dump())
    db.add(engineer)
    db.commit()
    db.refresh(engineer)
    return engineer


@app.get("/engineers", response_model=list[EngineerRead])
def list_engineers(db: Session = Depends(get_db)) -> list[Engineer]:
    return list_engineers_with_runtime_health(db, settings.engineer_heartbeat_timeout_seconds)


@app.get("/engineers/{engineer_id}", response_model=EngineerRead)
def get_engineer(engineer_id: int, db: Session = Depends(get_db)) -> Engineer:
    engineer = get_engineer_or_404(db, engineer_id)
    return refresh_engineer_runtime_health(db, engineer, settings.engineer_heartbeat_timeout_seconds)


@app.patch("/engineers/{engineer_id}", response_model=EngineerRead)
def patch_engineer(engineer_id: int, payload: EngineerUpdate, db: Session = Depends(get_db)) -> Engineer:
    engineer = get_engineer_or_404(db, engineer_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(engineer, field, value)
    db.add(engineer)
    db.commit()
    db.refresh(engineer)
    return engineer


@app.delete("/engineers/{engineer_id}")
def delete_engineer_route(engineer_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    engineer = refresh_engineer_runtime_health(
        db,
        get_engineer_or_404(db, engineer_id),
        settings.engineer_heartbeat_timeout_seconds,
    )
    if any(
        runtime.runtime_status in {
            EngineerRuntimeStatus.STARTING,
            EngineerRuntimeStatus.HEALTHY,
            EngineerRuntimeStatus.HEARTBEAT_MISSING,
        }
        for runtime in engineer.runtimes
    ):
        raise HTTPException(status_code=400, detail="Cannot delete a running engineer. Stop the runtime first.")
    delete_engineer(db, engineer_id)
    return {"deleted": True}


@app.post("/engineers/{engineer_id}/launch", response_model=EngineerRead)
def launch_engineer(engineer_id: int, db: Session = Depends(get_db)) -> Engineer:
    engineer = get_engineer_or_404(db, engineer_id)
    provider_key = f"{engineer.model_provider}_api_key"
    provider_api_key = get_config_setting_by_key(db, provider_key).value
    provider_env_var = PROVIDER_ENV_VAR_MAP[ModelProvider(engineer.model_provider)]
    github_token_setting = get_optional_config_setting_by_key(db, "github_developer_token")
    github_token = github_token_setting.value if github_token_setting else ""
    aws_access_key_id_setting = get_optional_config_setting_by_key(db, "aws_access_key_id")
    aws_secret_access_key_setting = get_optional_config_setting_by_key(db, "aws_secret_access_key")
    aws_region_setting = get_optional_config_setting_by_key(db, "aws_region")
    runtime = find_reusable_engineer_runtime(engineer) or create_engineer_runtime(db, engineer)
    try:
        container_name, container_id = runtime_manager.launch_engineer(
            engineer,
            runtime,
            provider_api_key,
            provider_env_var,
            github_token,
            aws_access_key_id_setting.value if aws_access_key_id_setting else "",
            aws_secret_access_key_setting.value if aws_secret_access_key_setting else "",
            aws_region_setting.value if aws_region_setting else "",
        )
        mark_engineer_runtime_launching(db, runtime, container_name, container_id)
    except Exception:
        runtime.runtime_status = EngineerRuntimeStatus.LAUNCH_FAILED
        runtime.status_message = "Runtime launch failed."
        db.add(runtime)
        db.commit()
        raise
    refreshed_engineer = refresh_engineer_runtime_health(
        db,
        get_engineer_or_404(db, engineer_id),
        settings.engineer_heartbeat_timeout_seconds,
    )
    return refreshed_engineer


@app.post("/engineer-runtimes/{runtime_id}/stop", response_model=EngineerRuntimeRead)
def stop_engineer_runtime(runtime_id: int, db: Session = Depends(get_db)) -> EngineerRuntime:
    runtime = get_engineer_runtime_or_404(db, runtime_id)
    runtime_manager.stop_engineer_runtime(runtime)
    return mark_engineer_runtime_stopped(db, runtime, "Runtime stopped by user.")


@app.post("/engineer-runtimes/{runtime_id}/restart", response_model=EngineerRuntimeRead)
def restart_engineer_runtime(runtime_id: int, db: Session = Depends(get_db)) -> EngineerRuntime:
    runtime = get_engineer_runtime_or_404(db, runtime_id)
    engineer = get_engineer_or_404(db, runtime.engineer_id)
    runtime_manager.stop_engineer_runtime(runtime)
    mark_engineer_runtime_stopped(db, runtime, "Runtime restarting.")
    provider_key = f"{engineer.model_provider}_api_key"
    provider_api_key = get_config_setting_by_key(db, provider_key).value
    provider_env_var = PROVIDER_ENV_VAR_MAP[ModelProvider(engineer.model_provider)]
    github_token_setting = get_optional_config_setting_by_key(db, "github_developer_token")
    github_token = github_token_setting.value if github_token_setting else ""
    aws_access_key_id_setting = get_optional_config_setting_by_key(db, "aws_access_key_id")
    aws_secret_access_key_setting = get_optional_config_setting_by_key(db, "aws_secret_access_key")
    aws_region_setting = get_optional_config_setting_by_key(db, "aws_region")
    try:
        container_name, container_id = runtime_manager.launch_engineer(
            engineer,
            runtime,
            provider_api_key,
            provider_env_var,
            github_token,
            aws_access_key_id_setting.value if aws_access_key_id_setting else "",
            aws_secret_access_key_setting.value if aws_secret_access_key_setting else "",
            aws_region_setting.value if aws_region_setting else "",
        )
        return mark_engineer_runtime_launching(db, runtime, container_name, container_id)
    except Exception:
        runtime.runtime_status = EngineerRuntimeStatus.LAUNCH_FAILED
        runtime.status_message = "Runtime restart failed."
        db.add(runtime)
        db.commit()
        raise


@app.post("/engineers/{engineer_id}/stop", response_model=EngineerRead)
def stop_engineer(engineer_id: int, db: Session = Depends(get_db)) -> Engineer:
    engineer = get_engineer_or_404(db, engineer_id)
    for runtime in engineer.runtimes:
        runtime_manager.stop_engineer_runtime(runtime)
        mark_engineer_runtime_stopped(db, runtime, "Runtime stopped by user.")
    return refresh_engineer_runtime_health(db, get_engineer_or_404(db, engineer_id), settings.engineer_heartbeat_timeout_seconds)


@app.post("/engineer-runtimes/{runtime_id}/heartbeat", response_model=EngineerRuntimeRead)
def engineer_runtime_heartbeat(runtime_id: int, payload: EngineerHeartbeat, db: Session = Depends(get_db)) -> EngineerRuntime:
    return record_engineer_runtime_heartbeat(
        db,
        runtime_id=runtime_id,
        container_name=payload.container_name,
        container_id=payload.container_id,
        status_message=payload.status_message,
    )


@app.post("/tasks", response_model=TaskRead)
def create_task_route(payload: TaskCreate, db: Session = Depends(get_db)) -> Task:
    task = create_task(db, payload)
    maybe_create_task_run(db, task)
    return get_task_or_404(db, task.id)


@app.patch("/tasks/{task_id}", response_model=TaskRead)
def patch_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)) -> Task:
    return update_task(db, task_id, payload)


@app.post("/tasks/{task_id}/retry", response_model=TaskRead)
def retry_task_route(task_id: int, db: Session = Depends(get_db)) -> Task:
    return retry_task(db, task_id)


@app.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db)) -> Task:
    return get_task_or_404(db, task_id)


@app.delete("/tasks/{task_id}")
def delete_task_route(task_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    delete_task(db, task_id)
    return {"deleted": True}


@app.get("/board", response_model=BoardRead)
def get_board(db: Session = Depends(get_db)) -> BoardRead:
    tasks = list_tasks_by_status(db)
    lanes = []
    for status in TaskStatus:
        lanes.append(BoardLane(status=status, tasks=[task for task in tasks if task.status == status]))
    return BoardRead(lanes=lanes)


@app.get("/overview/attention-tasks", response_model=list[TaskRead])
def get_attention_tasks(db: Session = Depends(get_db)) -> list[Task]:
    return list_attention_tasks(db)


@app.get("/projects/{project_id}/board", response_model=BoardRead)
def get_project_board(project_id: int, db: Session = Depends(get_db)) -> BoardRead:
    project = get_project_or_404(db, project_id)
    tasks = list_tasks_by_status(db, project_id=project_id)

    if project.workflow_id:
        workflow = db.scalar(
            select(Workflow).options(selectinload(Workflow.stages)).where(Workflow.id == project.workflow_id)
        )
        if workflow and workflow.stages:
            lanes = []
            for stage in sorted(workflow.stages, key=lambda s: s.stage_order):
                tasks_in_stage = [task for task in tasks if task.workflow_stage_id == stage.id]
                lanes.append(BoardLane(status=TaskStatus.DRAFT, tasks=tasks_in_stage))
            return BoardRead(lanes=lanes)

    lanes = []
    for status in TaskStatus:
        lanes.append(BoardLane(status=status, tasks=[task for task in tasks if task.status == status]))
    return BoardRead(lanes=lanes)


@app.post("/tasks/{task_id}/comments", response_model=TaskCommentRead)
def create_task_comment(task_id: int, payload: TaskCommentCreate, db: Session = Depends(get_db)) -> TaskCommentRead:
    return add_comment(db, task_id, payload)


@app.delete("/tasks/{task_id}/comments/{comment_id}")
def delete_task_comment(task_id: int, comment_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    delete_comment(db, task_id, comment_id)
    return {"deleted": True}


@app.post("/task-runs/{task_run_id}/approve", response_model=TaskRunRead)
def approve_run(task_run_id: int, payload: TaskRunApprovalRequest, db: Session = Depends(get_db)) -> TaskRun:
    return approve_task_run(db, task_run_id, payload.summary)


@app.post("/task-runs/{task_run_id}/reject", response_model=TaskRunRead)
def reject_run(task_run_id: int, payload: TaskRunApprovalRequest, db: Session = Depends(get_db)) -> TaskRun:
    return reject_task_run(db, task_run_id, payload.summary)


@app.post("/agent/poll-next-task", response_model=AgentPollResponse)
def agent_poll(payload: AgentPollRequest, db: Session = Depends(get_db)) -> AgentPollResponse:
    task_run, task, runtime = poll_next_task(db, payload.runtime_id)
    if not task_run or not task or not runtime:
        return AgentPollResponse()
    project = get_project_or_404(db, task.project_id)
    engineer = get_engineer_or_404(db, runtime.engineer_id)
    task_bundle = build_task_bundle(task, project, engineer)
    stage = task.current_stage
    return AgentPollResponse(
        task_run=task_run,
        task=task,
        project=project,
        engineer=engineer,
        runtime=runtime,
        task_bundle=task_bundle,
        stage=stage,
    )


@app.post("/agent/task-runs/{task_run_id}/heartbeat", response_model=TaskRunRead)
def agent_heartbeat(task_run_id: int, payload: AgentHeartbeat, db: Session = Depends(get_db)) -> TaskRun:
    return update_heartbeat(db, task_run_id, payload.status, payload.summary)


@app.post("/agent/task-runs/{task_run_id}/logs", response_model=TaskCommentRead)
def agent_logs(task_run_id: int, payload: AgentLog, db: Session = Depends(get_db)) -> TaskCommentRead:
    return add_agent_log(db, task_run_id, payload.body, payload.author_name, payload.action_required)


@app.post("/agent/task-runs/{task_run_id}/outcome", response_model=TaskRunRead)
def agent_outcome(task_run_id: int, payload: AgentOutcome, db: Session = Depends(get_db)) -> TaskRun:
    return apply_agent_outcome(db, task_run_id, payload)


@app.post("/artifacts/upload")
def upload_artifact(
    task_id: int = Form(...),
    kind: ArtifactKind = Form(...),
    task_run_id: int | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    artifact = store_artifact(db, storage, task_id, task_run_id, kind, file)
    return {"artifact_id": artifact.id, "file_path": artifact.file_path}


# ---- Organization routes ----
@app.get("/organizations", response_model=list[OrganizationRead])
def list_orgs(db: Session = Depends(get_db)) -> list[Organization]:
    return list_organizations(db)

@app.get("/organizations/{org_id}", response_model=OrganizationRead)
def get_org(org_id: int, db: Session = Depends(get_db)) -> Organization:
    return get_organization_or_404(db, org_id)

@app.post("/organizations", response_model=OrganizationRead)
def create_org(payload: OrganizationCreate, db: Session = Depends(get_db)) -> Organization:
    creator_email = "admin@devboss.local"
    return create_organization(db, payload.name, payload.slug, creator_email)

@app.patch("/organizations/{org_id}", response_model=OrganizationRead)
def patch_org(org_id: int, payload: OrganizationUpdate, db: Session = Depends(get_db)) -> Organization:
    org = get_organization_or_404(db, org_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(org, field, value)
    org.updated_at = datetime.now()
    db.add(org)
    db.commit()
    return get_organization_or_404(db, org_id)

@app.delete("/organizations/{org_id}")
def delete_org(org_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    delete_organization_svc(db, org_id)
    return {"deleted": True}

@app.post("/organizations/{org_id}/members", response_model=OrganizationMemberRead)
def add_member(org_id: int, payload: OrgMemberCreate, db: Session = Depends(get_db)) -> OrganizationMember:
    return add_org_member(db, org_id, payload.user_email, payload.role)

@app.delete("/organizations/{org_id}/members/{member_id}")
def remove_member(org_id: int, member_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    remove_org_member(db, org_id, member_id)
    return {"deleted": True}

@app.patch("/organizations/{org_id}/members/{member_id}/role", response_model=OrganizationMemberRead)
def patch_member_role(org_id: int, member_id: int, payload: OrgMemberCreate, db: Session = Depends(get_db)) -> OrganizationMember:
    return update_org_member_role(db, org_id, member_id, payload.role)

# ---- PRD routes ----
@app.get("/prds", response_model=list[PRDRead])
def list_prds_route(org_id: int | None = None, db: Session = Depends(get_db)) -> list[PRD]:
    return list_prds(db, org_id)

@app.get("/prds/{prd_id}", response_model=PRDRead)
def get_prd(prd_id: int, db: Session = Depends(get_db)) -> PRD:
    return get_prd_or_404(db, prd_id)

@app.post("/prds", response_model=PRDRead)
def create_prd_route(payload: PRDCreate, db: Session = Depends(get_db)) -> PRD:
    return create_prd(db, payload.organization_id, payload.title, payload.summary, "admin@devboss.local")

@app.patch("/prds/{prd_id}", response_model=PRDRead)
def patch_prd(prd_id: int, payload: PRDUpdate, db: Session = Depends(get_db)) -> PRD:
    return update_prd(db, prd_id, payload.model_dump(exclude_unset=True))

@app.delete("/prds/{prd_id}")
def delete_prd_route(prd_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    prd = get_prd_or_404(db, prd_id)
    db.delete(prd)
    db.commit()
    return {"deleted": True}

@app.post("/prds/{prd_id}/comments", response_model=PRDCommentRead)
def create_prd_comment(prd_id: int, payload: PRDCommentCreate, db: Session = Depends(get_db)) -> PRDComment:
    return add_prd_comment(db, prd_id, CommentAuthorType.HUMAN, "User", payload.body)

@app.post("/prds/{prd_id}/chat", response_model=PRDCommentRead)
def prd_chat(prd_id: int, payload: PRDChatMessage, db: Session = Depends(get_db)) -> PRDComment:
    add_prd_comment(db, prd_id, CommentAuthorType.HUMAN, "User", payload.message)
    prd = get_prd_or_404(db, prd_id)
    context = "\n".join([f"{c.author_name}: {c.body}" for c in prd.comments])
    reply = f"Thanks for your input. Here's what I've captured so far:\n\n---\n\n{prd.body_markdown or prd.summary or 'No content yet.'}\n\n---\n\nBased on your latest message: \"{payload.message}\"\n\nWhat would you like to refine or add next?"
    return add_prd_comment(db, prd_id, CommentAuthorType.AGENT, "Dev Boss", reply)

@app.patch("/prds/{prd_id}/body", response_model=PRDRead)
def update_prd_body(prd_id: int, payload: PRDUpdate, db: Session = Depends(get_db)) -> PRD:
    return update_prd(db, prd_id, {"body_markdown": payload.body_markdown})

@app.post("/prds/{prd_id}/convert", response_model=list[TaskRead])
def convert_prd(prd_id: int, payload: PRDConvertRequest, db: Session = Depends(get_db)) -> list[Task]:
    tasks = convert_prd_to_tasks(db, prd_id, payload.project_ids, payload.task_titles)
    return [get_task_or_404(db, t.id) for t in tasks]

# ---- Token routes ----
@app.post("/token-usage", response_model=TokenUsageRead)
def create_token_usage(payload: TokenUsageCreate, db: Session = Depends(get_db)) -> TokenUsage:
    return record_token_usage(db, None, payload.task_id, payload.task_run_id, payload.prd_id, payload.model, payload.tokens_in, payload.tokens_out, payload.cost_usd)

@app.get("/projects/{project_id}/token-summary", response_model=TokenSummary)
def project_token_summary(project_id: int, db: Session = Depends(get_db)) -> TokenSummary:
    get_project_or_404(db, project_id)
    return get_project_token_summary(db, project_id)

@app.get("/tasks/{task_id}/token-summary", response_model=TokenSummary)
def task_token_summary_route(task_id: int, db: Session = Depends(get_db)) -> TokenSummary:
    get_task_or_404(db, task_id)
    return get_task_token_summary(db, task_id)

# ---- Tag routes ----
@app.post("/tags", response_model=TagRead)
def create_tag(payload: TagCreate, db: Session = Depends(get_db)) -> Tag:
    return create_tag_svc(db, payload.organization_id, payload.name, payload.color)

@app.get("/organizations/{org_id}/tags", response_model=list[TagRead])
def list_org_tags(org_id: int, db: Session = Depends(get_db)) -> list[Tag]:
    org = get_organization_or_404(db, org_id)
    return org.tags

@app.delete("/tags/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    delete_tag_svc(db, tag_id)
    return {"deleted": True}

@app.patch("/tasks/{task_id}/tags", response_model=list[TagRead])
def update_task_tags(task_id: int, payload: TaskTagsUpdate, db: Session = Depends(get_db)) -> list[Tag]:
    return set_task_tags(db, task_id, payload.tag_ids)

@app.patch("/prds/{prd_id}/tags", response_model=list[TagRead])
def update_prd_tags(prd_id: int, payload: PRDTagsUpdate, db: Session = Depends(get_db)) -> list[Tag]:
    return set_prd_tags(db, prd_id, payload.tag_ids)
