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
    NEEDS_HUMAN_INPUT = "needs_human_input"
    GROOMING_COMPLETE = "grooming_complete"
    BUILD_COMPLETE = "build_complete"
    TESTING_COMPLETE = "testing_complete"
    DEPLOYMENT_COMPLETE = "deployment_complete"
    BLOCKED = "blocked"
    FAILED = "failed"


class CommentAuthorType(str, Enum):
    HUMAN = "human"
    AGENT = "agent"
    SYSTEM = "system"


class ArtifactKind(str, Enum):
    LOG = "log"
    TEST_REPORT = "test_report"
    SCREENSHOT = "screenshot"
    TRANSCRIPT = "transcript"
    ATTACHMENT = "attachment"
    DEPLOY_EVIDENCE = "deploy_evidence"
