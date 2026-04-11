from app.enums import OutcomeType, RunPhase, TaskStatus


ALLOWED_STATUS_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.DRAFT: {TaskStatus.AI_GROOMING, TaskStatus.ARCHIVED},
    TaskStatus.AI_GROOMING: {TaskStatus.READY_FOR_BUILD, TaskStatus.ARCHIVED},
    TaskStatus.READY_FOR_BUILD: {TaskStatus.IN_PROGRESS, TaskStatus.ARCHIVED},
    TaskStatus.IN_PROGRESS: {TaskStatus.AI_TESTING, TaskStatus.ARCHIVED},
    TaskStatus.AI_TESTING: {TaskStatus.HUMAN_TESTING, TaskStatus.ARCHIVED},
    TaskStatus.HUMAN_TESTING: {TaskStatus.READY_TO_DEPLOY, TaskStatus.ARCHIVED},
    TaskStatus.READY_TO_DEPLOY: {TaskStatus.DEPLOYED, TaskStatus.ARCHIVED},
    TaskStatus.DEPLOYED: {TaskStatus.ARCHIVED},
    TaskStatus.ARCHIVED: set(),
}


STATUS_PHASE_MAP: dict[TaskStatus, RunPhase | None] = {
    TaskStatus.DRAFT: None,
    TaskStatus.AI_GROOMING: RunPhase.GROOMING,
    TaskStatus.READY_FOR_BUILD: None,
    TaskStatus.IN_PROGRESS: RunPhase.BUILD,
    TaskStatus.AI_TESTING: RunPhase.TESTING,
    TaskStatus.HUMAN_TESTING: None,
    TaskStatus.READY_TO_DEPLOY: RunPhase.READY_TO_DEPLOY,
    TaskStatus.DEPLOYED: RunPhase.DEPLOYMENT,
    TaskStatus.ARCHIVED: None,
}


PHASE_STATUS_MAP: dict[RunPhase, TaskStatus] = {
    RunPhase.GROOMING: TaskStatus.AI_GROOMING,
    RunPhase.BUILD: TaskStatus.IN_PROGRESS,
    RunPhase.TESTING: TaskStatus.AI_TESTING,
    RunPhase.READY_TO_DEPLOY: TaskStatus.READY_TO_DEPLOY,
    RunPhase.DEPLOYMENT: TaskStatus.DEPLOYED,
}


OUTCOME_TO_STATUS: dict[OutcomeType, TaskStatus | None] = {
    OutcomeType.NEEDS_HUMAN_INPUT: None,
    OutcomeType.GROOMING_COMPLETE: TaskStatus.READY_FOR_BUILD,
    OutcomeType.BUILD_COMPLETE: TaskStatus.AI_TESTING,
    OutcomeType.TESTING_COMPLETE: TaskStatus.HUMAN_TESTING,
    OutcomeType.DEPLOYMENT_COMPLETE: TaskStatus.DEPLOYED,
    OutcomeType.BLOCKED: None,
    OutcomeType.FAILED: None,
}


ALLOWED_OUTCOMES_BY_STATUS: dict[TaskStatus, set[OutcomeType]] = {
    TaskStatus.AI_GROOMING: {
        OutcomeType.NEEDS_HUMAN_INPUT,
        OutcomeType.GROOMING_COMPLETE,
        OutcomeType.BLOCKED,
        OutcomeType.FAILED,
    },
    TaskStatus.IN_PROGRESS: {
        OutcomeType.NEEDS_HUMAN_INPUT,
        OutcomeType.BUILD_COMPLETE,
        OutcomeType.BLOCKED,
        OutcomeType.FAILED,
    },
    TaskStatus.AI_TESTING: {
        OutcomeType.NEEDS_HUMAN_INPUT,
        OutcomeType.TESTING_COMPLETE,
        OutcomeType.BLOCKED,
        OutcomeType.FAILED,
    },
    TaskStatus.READY_TO_DEPLOY: {
        OutcomeType.NEEDS_HUMAN_INPUT,
        OutcomeType.DEPLOYMENT_COMPLETE,
        OutcomeType.BLOCKED,
        OutcomeType.FAILED,
    },
    TaskStatus.DEPLOYED: {
        OutcomeType.NEEDS_HUMAN_INPUT,
        OutcomeType.DEPLOYMENT_COMPLETE,
        OutcomeType.BLOCKED,
        OutcomeType.FAILED,
    },
}


def can_transition(current: TaskStatus, target: TaskStatus) -> bool:
    return target in ALLOWED_STATUS_TRANSITIONS[current]


def required_phase_for_status(status: TaskStatus) -> RunPhase | None:
    return STATUS_PHASE_MAP[status]


def is_allowed_outcome_for_status(status: TaskStatus, outcome: OutcomeType) -> bool:
    allowed = ALLOWED_OUTCOMES_BY_STATUS.get(status)
    if allowed is None:
        return False
    return outcome in allowed


def execution_status_for_phase(phase: RunPhase) -> TaskStatus:
    return PHASE_STATUS_MAP[phase]
