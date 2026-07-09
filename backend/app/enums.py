from enum import Enum


class TaskStatus(str, Enum):
    DRAFT = "draft"
    AI_GROOMING = "ai_grooming"
    READY_FOR_BUILD = "ready_for_build"
    IN_PROGRESS = "in_progress"
    AI_TESTING = "ai_testing"
    HUMAN_TESTING = "human_testing"
    READY_TO_DEPLOY = "ready_to_deploy"
    DEPLOYED = "deployed"
    ARCHIVED = "archived"


class StatusGroup(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"
    DONE = "done"


class EngineerTemplate(str, Enum):
    BACKEND = "backend_engineer"
    FRONTEND = "frontend_engineer"
    QA = "qa_test_engineer"
    DEVOPS = "devops_deployment_engineer"


class EngineerRuntimeStatus(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    HEALTHY = "healthy"
    HEARTBEAT_MISSING = "heartbeat_missing"
    LAUNCH_FAILED = "launch_failed"


class RunPhase(str, Enum):
    GROOMING = "grooming"
    BUILD = "build"
    TESTING = "testing"
    READY_TO_DEPLOY = "ready_to_deploy"
    DEPLOYMENT = "deployment"


class RunStatus(str, Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    RUNNING = "running"
    WAITING_HUMAN = "waiting_human"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class OutcomeType(str, Enum):
    COMPLETED = "completed"
    NEEDS_HUMAN_INPUT = "needs_human_input"
    BLOCKED = "blocked"
    FAILED = "failed"
    GROOMING_COMPLETE = "grooming_complete"
    BUILD_COMPLETE = "build_complete"
    TESTING_COMPLETE = "testing_complete"
    DEPLOYMENT_COMPLETE = "deployment_complete"


class CommentAuthorType(str, Enum):
    HUMAN = "human"
    AGENT = "agent"
    SYSTEM = "system"


class ModelProvider(str, Enum):
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    GOOGLE = "google"
    GROQ = "groq"


PROVIDER_ENV_VAR_MAP: dict[ModelProvider, str] = {
    ModelProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
    ModelProvider.OPENAI: "OPENAI_API_KEY",
    ModelProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
    ModelProvider.OPENROUTER: "OPENROUTER_API_KEY",
    ModelProvider.GOOGLE: "GOOGLE_API_KEY",
    ModelProvider.GROQ: "GROQ_API_KEY",
}


class ArtifactKind(str, Enum):
    LOG = "log"
    TEST_REPORT = "test_report"
    SCREENSHOT = "screenshot"
    TRANSCRIPT = "transcript"
    ATTACHMENT = "attachment"
    DEPLOY_EVIDENCE = "deploy_evidence"


class MembershipRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"


class PRDStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    CONVERTED = "converted"
    ARCHIVED = "archived"
