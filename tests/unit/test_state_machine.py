from deepresearch_agent.orchestration.state_machine import InvalidTransitionError, TaskStateMachine
from deepresearch_agent.schemas import ResearchTask, TaskStatus


def test_state_machine_allows_happy_path() -> None:
    task = ResearchTask(question="test")
    machine = TaskStateMachine()

    machine.transition(task, TaskStatus.READY)
    machine.transition(task, TaskStatus.RUNNING)
    machine.transition(task, TaskStatus.SUCCEEDED)
    machine.transition(task, TaskStatus.VERIFIED)

    assert task.status == TaskStatus.VERIFIED


def test_state_machine_rejects_invalid_transition() -> None:
    task = ResearchTask(question="test")
    machine = TaskStateMachine()

    try:
        machine.transition(task, TaskStatus.SUCCEEDED)
    except InvalidTransitionError:
        return

    raise AssertionError("Expected InvalidTransitionError")


def test_state_machine_supports_timeout_retry_and_final_failure() -> None:
    task = ResearchTask(question="test")
    machine = TaskStateMachine()

    machine.transition(task, TaskStatus.READY)
    machine.transition(task, TaskStatus.RUNNING)
    machine.transition(task, TaskStatus.TIMED_OUT)
    machine.transition(task, TaskStatus.READY)
    machine.transition(task, TaskStatus.RUNNING)
    machine.transition(task, TaskStatus.TIMED_OUT)
    machine.transition(task, TaskStatus.FAILED)

    assert task.status == TaskStatus.FAILED
