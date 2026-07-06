from __future__ import annotations

from deepresearch_agent.schemas import ResearchTask, TaskStatus
from deepresearch_agent.schemas.core import utc_now


class InvalidTransitionError(ValueError):
    pass


class TaskStateMachine:
    _allowed: dict[TaskStatus, set[TaskStatus]] = {
        TaskStatus.PENDING: {TaskStatus.READY, TaskStatus.BLOCKED},
        TaskStatus.READY: {TaskStatus.RUNNING, TaskStatus.BLOCKED},
        TaskStatus.RUNNING: {TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.TIMED_OUT},
        TaskStatus.SUCCEEDED: {TaskStatus.VERIFIED, TaskStatus.REPAIRING},
        TaskStatus.FAILED: {TaskStatus.BLOCKED, TaskStatus.READY},
        TaskStatus.TIMED_OUT: {TaskStatus.READY, TaskStatus.FAILED, TaskStatus.BLOCKED},
        TaskStatus.REPAIRING: {TaskStatus.VERIFIED, TaskStatus.BLOCKED},
        TaskStatus.BLOCKED: {TaskStatus.READY},
        TaskStatus.VERIFIED: set(),
    }

    def transition(self, task: ResearchTask, target: TaskStatus) -> ResearchTask:
        if target not in self._allowed[task.status]:
            raise InvalidTransitionError(f"Cannot transition {task.id} from {task.status} to {target}")
        task.status = target
        task.updated_at = utc_now()
        return task
