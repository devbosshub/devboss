from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.enums import (
    ArtifactKind,
    CommentAuthorType,
    EngineerRuntimeStatus,
    EngineerTemplate,
    MembershipRole,
    ModelProvider,
    OutcomeType,
    PRDStatus,
    RunPhase,
    RunStatus,
    StatusGroup,
    TaskStatus,
)


class WorkflowStageCreate(BaseModel):
    name: str
    stage_order: int | None = None
    assigned_engineer_id: int | None = None
    requires_human_approval: bool = False
    is_ai_executable: bool = True
    stage_instructions: str | None = None
    max_rework_attempts: int = 3
    rework_target_stage_id: int | None = None


class WorkflowStageRead(BaseModel):
    id: int
    workflow_id: int
    name: str
    stage_order: int
    assigned_engineer_id: int | None = None
    requires_human_approval: bool
    is_ai_executable: bool
    stage_instructions: str | None = None
    max_rework_attempts: int
    rework_target_stage_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowStageUpdate(BaseModel):
    name: str | None = None
    stage_order: int | None = None
    assigned_engineer_id: int | None = None
    requires_human_approval: bool | None = None
    is_ai_executable: bool | None = None
    stage_instructions: str | None = None
    max_rework_attempts: int | None = None
    rework_target_stage_id: int | None = None


class WorkflowCreate(BaseModel):
    name: str
    description: str | None = None


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class WorkflowRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    stages: list[WorkflowStageRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StageReorderItem(BaseModel):
    id: int
    stage_order: int


class StageReorderRequest(BaseModel):
    stages: list[StageReorderItem]


class ProjectBase(BaseModel):
    name: str
    repo_url: str
    default_branch: str = "main"
    deploy_config: dict = Field(default_factory=dict)
    deployment_instructions: str = ""
    engineer_pool: list[str] = Field(default_factory=list)
    workflow_id: int | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = None
    repo_url: str | None = None
    default_branch: str | None = None
    deploy_config: dict | None = None
    deployment_instructions: str | None = None
    engineer_pool: list[str] | None = None
    workflow_id: int | None = None


class ProjectRead(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EngineerBase(BaseModel):
    name: str
    template: EngineerTemplate
    skill_markdown: str
    model_provider: ModelProvider = ModelProvider.DEEPSEEK
    model_name: str = "deepseek-v4-pro"
    docker_image: str = "devboss-engineer:latest"
    poll_interval_seconds: int = 30
    allowed_projects: list[str] = Field(default_factory=list)
    is_active: bool = True


class EngineerCreate(EngineerBase):
    pass


class EngineerUpdate(BaseModel):
    name: str | None = None
    template: EngineerTemplate | None = None
    skill_markdown: str | None = None
    model_provider: ModelProvider | None = None
    model_name: str | None = None
    docker_image: str | None = None
    poll_interval_seconds: int | None = None
    allowed_projects: list[str] | None = None
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
    workflow_stage_id: int | None = None
    status: RunStatus
    outcome_type: OutcomeType | None = None
    summary: str | None = None
    outcome_payload_json: dict | None = None
    transcript_path: str | None = None
    attempt_number: int = 1
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
    status_group: StatusGroup = StatusGroup.TODO
    workflow_stage_id: int | None = None
    branch_name: str | None = None
    pr_url: str | None = None
    deploy_url: str | None = None
    blocked_reason: str | None = None
    release_queue_entered_at: datetime | None = None
    testing_rework_count: int = 0
    rework_count: int = 0
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
    stage: WorkflowStageRead | None = None


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


# Organization schemas
class UserRead(BaseModel):
    id: int
    email: str
    name: str | None
    external_id: int | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class OrganizationMemberRead(BaseModel):
    id: int
    organization_id: int
    user_id: int
    role: MembershipRole
    user: UserRead | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class OrganizationCreate(BaseModel):
    name: str
    slug: str


class OrganizationUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None


class OrganizationRead(BaseModel):
    id: int
    name: str
    slug: str
    members: list[OrganizationMemberRead] = Field(default_factory=list)
    tags: list[TagRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class OrgMemberCreate(BaseModel):
    user_email: str
    role: MembershipRole = MembershipRole.MEMBER


# PRD schemas
class PRDCommentCreate(BaseModel):
    body: str


class PRDCommentRead(BaseModel):
    id: int
    prd_id: int
    author_type: CommentAuthorType
    author_name: str
    body: str
    created_at: datetime
    model_config = {"from_attributes": True}


class PRDCreate(BaseModel):
    organization_id: int
    title: str
    summary: str | None = None


class PRDUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    body_markdown: str | None = None
    status: PRDStatus | None = None


class PRDRead(BaseModel):
    id: int
    organization_id: int
    title: str
    summary: str | None
    body_markdown: str | None
    status: PRDStatus
    created_by_user_id: int | None
    comments: list[PRDCommentRead] = Field(default_factory=list)
    tags: list[TagRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class PRDChatMessage(BaseModel):
    message: str


class PRDConvertRequest(BaseModel):
    project_ids: list[int]
    task_titles: list[str]


# Token schemas
class TokenUsageCreate(BaseModel):
    task_id: int | None = None
    task_run_id: int | None = None
    prd_id: int | None = None
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0


class TokenUsageRead(BaseModel):
    id: int
    user_id: int | None
    task_id: int | None
    task_run_id: int | None
    prd_id: int | None
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    created_at: datetime
    model_config = {"from_attributes": True}


class TokenSummary(BaseModel):
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_cost_usd: float = 0.0


# Tag schemas
class TagCreate(BaseModel):
    organization_id: int
    name: str
    color: str | None = None


class TagRead(BaseModel):
    id: int
    organization_id: int
    name: str
    color: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class TaskTagsUpdate(BaseModel):
    tag_ids: list[int]


class PRDTagsUpdate(BaseModel):
    tag_ids: list[int]
