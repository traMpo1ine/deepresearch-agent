from __future__ import annotations

from collections import defaultdict, deque

from deepresearch_agent.schemas import ResearchTask
from deepresearch_agent.schemas import TaskStatus


class DAGCycleError(ValueError):
    pass


class DAGTaskGraph:
    def __init__(self, tasks: list[ResearchTask]) -> None:
        self.tasks = {task.id: task for task in tasks}
        self.children: dict[str, list[str]] = defaultdict(list)
        self.indegree: dict[str, int] = {task.id: 0 for task in tasks}
        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id not in self.tasks:
                    raise KeyError(f"Unknown dependency {dep_id} for task {task.id}")
                self.children[dep_id].append(task.id)
                self.indegree[task.id] += 1
        self._assert_acyclic()

    def _assert_acyclic(self) -> None:
        seen = 0
        queue = deque([task_id for task_id, degree in self.indegree.items() if degree == 0])
        indegree = dict(self.indegree)
        while queue:
            task_id = queue.popleft()
            seen += 1
            for child_id in self.children[task_id]:
                indegree[child_id] -= 1
                if indegree[child_id] == 0:
                    queue.append(child_id)
        if seen != len(self.tasks):
            raise DAGCycleError("Task graph contains a cycle.")

    def topological_batches(self) -> list[list[ResearchTask]]:
        batches: list[list[ResearchTask]] = []
        indegree = dict(self.indegree)
        queue = deque([task_id for task_id, degree in indegree.items() if degree == 0])
        while queue:
            batch_ids = list(queue)
            queue.clear()
            batches.append([self.tasks[task_id] for task_id in batch_ids])
            for task_id in batch_ids:
                for child_id in self.children[task_id]:
                    indegree[child_id] -= 1
                    if indegree[child_id] == 0:
                        queue.append(child_id)
        return batches

    def dependencies_succeeded(self, task: ResearchTask) -> bool:
        return all(
            self.tasks[dep_id].status in {TaskStatus.SUCCEEDED, TaskStatus.VERIFIED}
            for dep_id in task.dependencies
        )

    def mark_blocked_descendants(self, task_id: str) -> list[ResearchTask]:
        blocked: list[ResearchTask] = []
        for child_id in self.children.get(task_id, []):
            child = self.tasks[child_id]
            if child.status not in {TaskStatus.SUCCEEDED, TaskStatus.VERIFIED, TaskStatus.FAILED}:
                child.status = TaskStatus.BLOCKED
                blocked.append(child)
            blocked.extend(self.mark_blocked_descendants(child_id))
        return blocked
