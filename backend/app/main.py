from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Base, engine, get_db
from app.enums import ArtifactKind, EngineerRuntimeStatus, RunStatus, TaskStatus
from app.models import ConfigSetting, Engineer, EngineerRuntime, Project, Task, TaskRun
from app.schemas import (
    AgentHeartbeat,
    AgentLog,
    AgentOutcome,
    AgentPollRequest,
    AgentPollResponse,
    BoardLane,
    BoardRead,
    ConfigSettingCreate,
    EngineerHeartbeat,
    ConfigSettingRead,
    ConfigSettingUpdate,
    EngineerCreate,
    EngineerRead,
    EngineerRuntimeRead,
    EngineerUpdate,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    TaskCommentCreate,
    TaskCommentRead,
    TaskCreate,
    TaskRead,
    TaskRunApprovalRequest,
    TaskRunRead,
    TaskUpdate,
)
from app.runtime_manager import DockerRuntimeManager
from app.seed import seed_demo_workspace, seed_engineers
from app.services import (
    add_agent_log,
    add_comment,
    apply_agent_outcome,
    approve_task_run,
    create_engineer_runtime,
    delete_comment,
    delete_engineer,
    delete_project,
    delete_task,
    build_task_bundle,
    create_config_setting,
    delete_config_setting,
    create_task,
    get_config_setting_by_key,
    get_engineer_or_404,
    get_engineer_runtime_or_404,
    get_optional_config_setting_by_key,
    get_project_or_404,
    get_task_or_404,
    list_engineers_with_runtime_health,
    list_attention_tasks,
    list_config_settings,
    list_tasks_by_status,
    mark_engineer_runtime_launching,
    mark_engineer_runtime_stopped,
    maybe_create_task_run,
    poll_next_task,
    record_engineer_runtime_heartbeat,
    refresh_engineer_runtime_health,
    reject_task_run,
    retry_task,
    store_artifact,
    update_config_setting,
    update_heartbeat,
    update_task,
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
    if "engineer_runtimes" in runtime_tables and "current_task_run_id" not in runtime_columns:
        statements.append("ALTER TABLE engineer_runtimes ADD COLUMN current_task_run_id INTEGER")

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
    codex_auth_json = get_config_setting_by_key(db, "codex_auth_json").value
    github_token_setting = get_optional_config_setting_by_key(db, "github_developer_token")
    github_token = github_token_setting.value if github_token_setting else ""
    aws_access_key_id_setting = get_optional_config_setting_by_key(db, "aws_access_key_id")
    aws_secret_access_key_setting = get_optional_config_setting_by_key(db, "aws_secret_access_key")
    aws_region_setting = get_optional_config_setting_by_key(db, "aws_region")
    runtime = create_engineer_runtime(db, engineer)
    try:
        container_name, container_id = runtime_manager.launch_engineer(
            engineer,
            runtime,
            codex_auth_json,
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
    codex_auth_json = get_config_setting_by_key(db, "codex_auth_json").value
    github_token_setting = get_optional_config_setting_by_key(db, "github_developer_token")
    github_token = github_token_setting.value if github_token_setting else ""
    aws_access_key_id_setting = get_optional_config_setting_by_key(db, "aws_access_key_id")
    aws_secret_access_key_setting = get_optional_config_setting_by_key(db, "aws_secret_access_key")
    aws_region_setting = get_optional_config_setting_by_key(db, "aws_region")
    try:
        container_name, container_id = runtime_manager.launch_engineer(
            engineer,
            runtime,
            codex_auth_json,
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
    get_project_or_404(db, project_id)
    tasks = list_tasks_by_status(db, project_id=project_id)
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
    return AgentPollResponse(task_run=task_run, task=task, project=project, engineer=engineer, runtime=runtime, task_bundle=task_bundle)


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
