from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
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


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    stages: Mapped[list["WorkflowStage"]] = relationship(
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowStage.stage_order",
    )
    projects: Mapped[list["Project"]] = relationship(back_populates="workflow")


class WorkflowStage(Base):
    __tablename__ = "workflow_stages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflows.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    stage_order: Mapped[int] = mapped_column(Integer, nullable=False)
    assigned_engineer_id: Mapped[int | None] = mapped_column(ForeignKey("engineers.id"), nullable=True, index=True)
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    is_ai_executable: Mapped[bool] = mapped_column(Boolean, default=True)
    stage_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_rework_attempts: Mapped[int] = mapped_column(Integer, default=3)
    rework_target_stage_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_stages.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    workflow: Mapped["Workflow"] = relationship(back_populates="stages")
    assigned_engineer: Mapped["Engineer | None"] = relationship(foreign_keys=[assigned_engineer_id])
    rework_target: Mapped["WorkflowStage | None"] = relationship(remote_side=[id])
    tasks: Mapped[list["Task"]] = relationship(back_populates="current_stage")
    task_runs: Mapped[list["TaskRun"]] = relationship(back_populates="stage")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    repo_url: Mapped[str] = mapped_column(String(500))
    default_branch: Mapped[str] = mapped_column(String(128), default="main")
    deploy_config: Mapped[dict] = mapped_column(JSON, default=dict)
    deployment_instructions: Mapped[str] = mapped_column(Text, default="")
    engineer_pool: Mapped[list[str]] = mapped_column(JSON, default=list)
    workflow_id: Mapped[int | None] = mapped_column(ForeignKey("workflows.id"), nullable=True, index=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    tasks: Mapped[list["Task"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    workflow: Mapped["Workflow | None"] = relationship(back_populates="projects")
    organization: Mapped["Organization | None"] = relationship(back_populates="projects")


class Engineer(Base):
    __tablename__ = "engineers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    template: Mapped[EngineerTemplate] = mapped_column(Enum(EngineerTemplate))
    skill_markdown: Mapped[str] = mapped_column(Text)
    model_provider: Mapped[ModelProvider] = mapped_column(String(64), default=ModelProvider.DEEPSEEK)
    model_name: Mapped[str] = mapped_column(String(255), default="deepseek-v4-pro")
    docker_image: Mapped[str] = mapped_column(String(255), default="devboss-engineer:latest")
    poll_interval_seconds: Mapped[int] = mapped_column(Integer, default=30)
    allowed_projects: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    runtime_status: Mapped[EngineerRuntimeStatus] = mapped_column(String(64), default=EngineerRuntimeStatus.STOPPED, index=True)
    runtime_container_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    runtime_container_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    runtime_status_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    runtime_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    runtime_last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    tasks: Mapped[list["Task"]] = relationship(back_populates="assigned_engineer")
    task_runs: Mapped[list["TaskRun"]] = relationship(back_populates="engineer")
    runtimes: Mapped[list["EngineerRuntime"]] = relationship(
        back_populates="engineer",
        cascade="all, delete-orphan",
        order_by="EngineerRuntime.created_at",
    )


class EngineerRuntime(Base):
    __tablename__ = "engineer_runtimes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    engineer_id: Mapped[int] = mapped_column(ForeignKey("engineers.id"), index=True)
    runtime_status: Mapped[EngineerRuntimeStatus] = mapped_column(String(64), default=EngineerRuntimeStatus.STOPPED, index=True)
    container_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    container_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_task_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("task_runs.id", use_alter=True, name="fk_engineer_runtimes_current_task_run_id"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    engineer: Mapped["Engineer"] = relationship(back_populates="runtimes")
    current_task_run: Mapped["TaskRun | None"] = relationship(foreign_keys=[current_task_run_id])


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    assigned_engineer_id: Mapped[int | None] = mapped_column(ForeignKey("engineers.id"), nullable=True, index=True)
    workflow_stage_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_stages.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    requirement_markdown: Mapped[str] = mapped_column(Text)
    acceptance_criteria: Mapped[str] = mapped_column(Text)
    implementation_steps: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.DRAFT, index=True)
    status_group: Mapped[StatusGroup] = mapped_column(String(64), default=StatusGroup.TODO, index=True)
    branch_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pr_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    deploy_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    blocked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    release_queue_entered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    testing_rework_count: Mapped[int] = mapped_column(Integer, default=0)
    rework_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    project: Mapped[Project] = relationship(back_populates="tasks")
    assigned_engineer: Mapped[Engineer | None] = relationship(back_populates="tasks")
    current_stage: Mapped["WorkflowStage | None"] = relationship(back_populates="tasks", foreign_keys=[workflow_stage_id])
    comments: Mapped[list["TaskComment"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskComment.created_at",
    )
    task_runs: Mapped[list["TaskRun"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskRun.created_at",
    )
    artifacts: Mapped[list["EvidenceArtifact"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    tags: Mapped[list["Tag"]] = relationship(secondary="task_tags", back_populates="tasks")


class TaskComment(Base):
    __tablename__ = "task_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    author_type: Mapped[CommentAuthorType] = mapped_column(Enum(CommentAuthorType))
    author_name: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    action_required: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    task: Mapped[Task] = relationship(back_populates="comments")


class TaskRun(Base):
    __tablename__ = "task_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    engineer_id: Mapped[int] = mapped_column(ForeignKey("engineers.id"), index=True)
    claimed_by_runtime_id: Mapped[int | None] = mapped_column(
        ForeignKey("engineer_runtimes.id", use_alter=True, name="fk_task_runs_claimed_by_runtime_id"),
        nullable=True,
        index=True,
    )
    phase: Mapped[RunPhase] = mapped_column(Enum(RunPhase))
    workflow_stage_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_stages.id"), nullable=True, index=True)
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.PENDING, index=True)
    outcome_type: Mapped[OutcomeType | None] = mapped_column(Enum(OutcomeType), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome_payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    transcript_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    task: Mapped[Task] = relationship(back_populates="task_runs")
    engineer: Mapped[Engineer] = relationship(back_populates="task_runs")
    stage: Mapped["WorkflowStage | None"] = relationship(back_populates="task_runs")
    claimed_by_runtime: Mapped["EngineerRuntime | None"] = relationship(foreign_keys=[claimed_by_runtime_id])


class EvidenceArtifact(Base):
    __tablename__ = "evidence_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    task_run_id: Mapped[int | None] = mapped_column(ForeignKey("task_runs.id"), nullable=True, index=True)
    kind: Mapped[ArtifactKind] = mapped_column(Enum(ArtifactKind))
    name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    task: Mapped[Task] = relationship(back_populates="artifacts")


class ConfigSetting(Base):
    __tablename__ = "config_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    memberships: Mapped[list["OrganizationMember"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    token_usages: Mapped[list["TokenUsage"]] = relationship(back_populates="user")


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    members: Mapped[list["OrganizationMember"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    projects: Mapped[list["Project"]] = relationship(back_populates="organization")
    prds: Mapped[list["PRD"]] = relationship(back_populates="organization")
    tags: Mapped[list["Tag"]] = relationship(back_populates="organization", cascade="all, delete-orphan")


class OrganizationMember(Base):
    __tablename__ = "organization_members"
    __table_args__ = (UniqueConstraint("organization_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[MembershipRole] = mapped_column(String(32), default=MembershipRole.MEMBER)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    organization: Mapped["Organization"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="memberships")


class PRD(Base):
    __tablename__ = "prds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[PRDStatus] = mapped_column(String(32), default=PRDStatus.DRAFT, index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    organization: Mapped["Organization"] = relationship(back_populates="prds")
    created_by: Mapped["User | None"] = relationship(foreign_keys=[created_by_user_id])
    comments: Mapped[list["PRDComment"]] = relationship(back_populates="prd", cascade="all, delete-orphan", order_by="PRDComment.created_at")
    tags: Mapped[list["Tag"]] = relationship(secondary="prd_tags", back_populates="prds")
    token_usages: Mapped[list["TokenUsage"]] = relationship(back_populates="prd")


class PRDComment(Base):
    __tablename__ = "prd_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prd_id: Mapped[int] = mapped_column(ForeignKey("prds.id"), index=True)
    author_type: Mapped[CommentAuthorType] = mapped_column(Enum(CommentAuthorType))
    author_name: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    prd: Mapped["PRD"] = relationship(back_populates="comments")


class TokenUsage(Base):
    __tablename__ = "token_usages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"), nullable=True, index=True)
    task_run_id: Mapped[int | None] = mapped_column(ForeignKey("task_runs.id"), nullable=True, index=True)
    prd_id: Mapped[int | None] = mapped_column(ForeignKey("prds.id"), nullable=True, index=True)
    model: Mapped[str] = mapped_column(String(128))
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User | None"] = relationship(back_populates="token_usages")
    task: Mapped["Task | None"] = relationship()
    task_run: Mapped["TaskRun | None"] = relationship()
    prd: Mapped["PRD | None"] = relationship(back_populates="token_usages")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    color: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    organization: Mapped["Organization"] = relationship(back_populates="tags")
    tasks: Mapped[list["Task"]] = relationship(secondary="task_tags", back_populates="tags")
    prds: Mapped[list["PRD"]] = relationship(secondary="prd_tags", back_populates="tags")


task_tags = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

prd_tags = Table(
    "prd_tags",
    Base.metadata,
    Column("prd_id", ForeignKey("prds.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)
