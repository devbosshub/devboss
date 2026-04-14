from datetime import datetime

from pydantic import BaseModel, Field

from app.enums import (
    ArtifactKind,
    CommentAuthorType,
    EngineerRuntimeStatus,
    EngineerTemplate,
    OutcomeType,
    RunPhase,
    RunStatus,
    TaskStatus,
)


class ProjectBase(BaseModel):
    name: str
    repo_url: str
    default_branch: str = "main"
    deploy_config: dict = Field(default_factory=dict)
    deployment_instructions: str = ""
    engineer_pool: list[str] = Field(default_factory=list)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = None
    repo_url: str | None = None
    default_branch: str | None = None
    deploy_config: dict | None = None
    deployment_instructions: str | None = None
    engineer_pool: list[str] | None = None


class ProjectRead(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EngineerBase(BaseModel):
    name: str
    template: EngineerTemplate
    skill_markdown: str
    model_name: str = "gpt-5.4"
    docker_image: str = "devboss-engineer:latest"
    poll_interval_seconds: int = 30
    enabled_tools: list[str] = Field(default_factory=list)
    allowed_projects: list[str] = Field(default_factory=list)
    runtime_config: dict = Field(default_factory=dict)
    is_active: bool = True


class EngineerCreate(EngineerBase):
    pass


class EngineerUpdate(BaseModel):
    name: str | None = None
    template: EngineerTemplate | None = None
    skill_markdown: str | None = None
    model_name: str | None = None
    docker_image: str | None = None
    poll_interval_seconds: int | None = None
    enabled_tools: list[str] | None = None
    allowed_projects: list[str] | None = None
    runtime_config: dict | None = None
    is_active: bool | None = None


class EngineerRuntimeRead(BaseModel):
    id: int
    engineer_id: int
    runtime_status: EngineerRuntimeStatus
    container_name: str | None = None
    container_id: str | None = None
    status_message: str | None = None
    started_at: datetime | None = None
    last_heartbeat_at: datetime | None = None
    current_task_run_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EngineerRead(EngineerBase):
    id: int
    runtime_status: EngineerRuntimeStatus
    runtime_container_name: str | None = None
    runtime_container_id: str | None = None
    runtime_status_message: str | None = None
    runtime_started_at: datetime | None = None
    runtime_last_heartbeat_at: datetime | None = None
    runtime_count: int = 0
    healthy_runtime_count: int = 0
    busy_runtime_count: int = 0
    runtimes: list[EngineerRuntimeRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EngineerHeartbeat(BaseModel):
    container_name: str
    container_id: str | None = None
    status_message: str | None = None


class TaskBase(BaseModel):
    project_id: int
    assigned_engineer_id: int | None = None
    title: str
    requirement_markdown: str
    acceptance_criteria: str
    implementation_steps: str = ""


class TaskCreate(TaskBase):
    status: TaskStatus = TaskStatus.DRAFT


class TaskUpdate(BaseModel):
    assigned_engineer_id: int | None = None
    title: str | None = None
    requirement_markdown: str | None = None
    acceptance_criteria: str | None = None
    implementation_steps: str | None = None
    status: TaskStatus | None = None
    branch_name: str | None = None
    pr_url: str | None = None
    deploy_url: str | None = None
    blocked_reason: str | None = None


class TaskCommentCreate(BaseModel):
    author_type: CommentAuthorType
    author_name: str
    body: str
    action_required: bool = False


class TaskCommentRead(TaskCommentCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ArtifactRead(BaseModel):
    id: int
    task_id: int
    task_run_id: int | None = None
    kind: ArtifactKind
    name: str
    file_path: str
    content_type: str | None = None
    metadata_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskRunRead(BaseModel):
    id: int
    task_id: int
    engineer_id: int
    claimed_by_runtime_id: int | None = None
    phase: RunPhase
    status: RunStatus
    outcome_type: OutcomeType | None = None
    summary: str | None = None
    outcome_payload_json: dict | None = None
    transcript_path: str | None = None
    claimed_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    heartbeat_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskRead(TaskBase):
    id: int
    status: TaskStatus
    branch_name: str | None = None
    pr_url: str | None = None
    deploy_url: str | None = None
    blocked_reason: str | None = None
    release_queue_entered_at: datetime | None = None
    testing_rework_count: int = 0
    created_at: datetime
    updated_at: datetime
    comments: list[TaskCommentRead] = Field(default_factory=list)
    task_runs: list[TaskRunRead] = Field(default_factory=list)
    artifacts: list[ArtifactRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class BoardLane(BaseModel):
    status: TaskStatus
    tasks: list[TaskRead]


class BoardRead(BaseModel):
    lanes: list[BoardLane]


class TaskRunApprovalRequest(BaseModel):
    summary: str | None = None


class AgentPollRequest(BaseModel):
    runtime_id: int


class AgentPollResponse(BaseModel):
    task_run: TaskRunRead | None = None
    task: TaskRead | None = None
    project: ProjectRead | None = None
    engineer: EngineerRead | None = None
    task_bundle: dict | None = None
    runtime: EngineerRuntimeRead | None = None


class AgentHeartbeat(BaseModel):
    status: RunStatus | None = None
    summary: str | None = None


class AgentLog(BaseModel):
    body: str
    author_name: str = "agent-runtime"
    action_required: bool = False


class AgentOutcome(BaseModel):
    outcome_type: OutcomeType
    summary: str
    branch_name: str | None = None
    pr_url: str | None = None
    deploy_url: str | None = None
    blocked_reason: str | None = None


class ConfigSettingBase(BaseModel):
    key: str
    value: str
    is_secret: bool = True
    description: str | None = None


class ConfigSettingCreate(ConfigSettingBase):
    pass


class ConfigSettingUpdate(BaseModel):
    value: str | None = None
    is_secret: bool | None = None
    description: str | None = None


class ConfigSettingRead(BaseModel):
    id: int
    key: str
    value: str
    is_secret: bool
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
