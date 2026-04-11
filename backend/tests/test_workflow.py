from app.enums import OutcomeType, TaskStatus
from app.workflow import OUTCOME_TO_STATUS, can_transition, is_allowed_outcome_for_status


def test_core_status_transitions():
    assert can_transition(TaskStatus.DRAFT, TaskStatus.AI_GROOMING)
    assert can_transition(TaskStatus.AI_GROOMING, TaskStatus.READY_FOR_BUILD)
    assert can_transition(TaskStatus.READY_FOR_BUILD, TaskStatus.IN_PROGRESS)
    assert can_transition(TaskStatus.IN_PROGRESS, TaskStatus.AI_TESTING)
    assert can_transition(TaskStatus.AI_TESTING, TaskStatus.HUMAN_TESTING)
    assert can_transition(TaskStatus.HUMAN_TESTING, TaskStatus.READY_TO_DEPLOY)
    assert can_transition(TaskStatus.READY_TO_DEPLOY, TaskStatus.DEPLOYED)


def test_invalid_transition_is_rejected():
    assert not can_transition(TaskStatus.DRAFT, TaskStatus.IN_PROGRESS)
    assert not can_transition(TaskStatus.DEPLOYED, TaskStatus.IN_PROGRESS)


def test_outcome_mapping():
    assert OUTCOME_TO_STATUS[OutcomeType.GROOMING_COMPLETE] == TaskStatus.READY_FOR_BUILD
    assert OUTCOME_TO_STATUS[OutcomeType.BUILD_COMPLETE] == TaskStatus.AI_TESTING
    assert OUTCOME_TO_STATUS[OutcomeType.TESTING_COMPLETE] == TaskStatus.HUMAN_TESTING
    assert OUTCOME_TO_STATUS[OutcomeType.DEPLOYMENT_COMPLETE] == TaskStatus.DEPLOYED


def test_stage_allows_only_matching_outcomes():
    assert is_allowed_outcome_for_status(TaskStatus.AI_GROOMING, OutcomeType.GROOMING_COMPLETE)
    assert not is_allowed_outcome_for_status(TaskStatus.AI_GROOMING, OutcomeType.BUILD_COMPLETE)
    assert is_allowed_outcome_for_status(TaskStatus.IN_PROGRESS, OutcomeType.BUILD_COMPLETE)
    assert is_allowed_outcome_for_status(TaskStatus.AI_TESTING, OutcomeType.TESTING_COMPLETE)
