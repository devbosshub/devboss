from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
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


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    repo_url: Mapped[str] = mapped_column(String(500))
    default_branch: Mapped[str] = mapped_column(String(128), default="main")
    deploy_config: Mapped[dict] = mapped_column(JSON, default=dict)
    deployment_instructions: Mapped[str] = mapped_column(Text, default="")
    engineer_pool: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    tasks: Mapped[list["Task"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Engineer(Base):
    __tablename__ = "engineers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    template: Mapped[EngineerTemplate] = mapped_column(Enum(EngineerTemplate))
    skill_markdown: Mapped[str] = mapped_column(Text)
    model_name: Mapped[str] = mapped_column(String(255), default="gpt-5.4")
    docker_image: Mapped[str] = mapped_column(String(255), default="devboss-engineer:latest")
    poll_interval_seconds: Mapped[int] = mapped_column(Integer, default=30)
    enabled_tools: Mapped[list[str]] = mapped_column(JSON, default=list)
    allowed_projects: Mapped[list[str]] = mapped_column(JSON, default=list)
    runtime_config: Mapped[dict] = mapped_column(JSON, default=dict)
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
    title: Mapped[str] = mapped_column(String(255), index=True)
    requirement_markdown: Mapped[str] = mapped_column(Text)
    acceptance_criteria: Mapped[str] = mapped_column(Text)
    implementation_steps: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.DRAFT, index=True)
    branch_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pr_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    deploy_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    blocked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    release_queue_entered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    testing_rework_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    project: Mapped[Project] = relationship(back_populates="tasks")
    assigned_engineer: Mapped[Engineer | None] = relationship(back_populates="tasks")
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
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.PENDING, index=True)
    outcome_type: Mapped[OutcomeType | None] = mapped_column(Enum(OutcomeType), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome_payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    transcript_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    task: Mapped[Task] = relationship(back_populates="task_runs")
    engineer: Mapped[Engineer] = relationship(back_populates="task_runs")
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
