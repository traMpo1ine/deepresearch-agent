import pytest

from deepresearch_agent.orchestration.dag import DAGCycleError, DAGTaskGraph
from deepresearch_agent.schemas import ResearchTask, TaskStatus


def test_dag_topological_batches_allow_parallel_layer() -> None:
    root = ResearchTask(question="root")
    left = ResearchTask(question="left", dependencies=[root.id])
    right = ResearchTask(question="right", dependencies=[root.id])
    final = ResearchTask(question="final", dependencies=[left.id, right.id])

    graph = DAGTaskGraph([root, left, right, final])
    batches = graph.topological_batches()

    assert [task.id for task in batches[0]] == [root.id]
    assert {task.id for task in batches[1]} == {left.id, right.id}
    assert [task.id for task in batches[2]] == [final.id]


def test_dag_cycle_detection() -> None:
    a = ResearchTask(question="a")
    b = ResearchTask(question="b", dependencies=[a.id])
    a.dependencies.append(b.id)

    with pytest.raises(DAGCycleError):
        DAGTaskGraph([a, b])


def test_blocked_descendants() -> None:
    root = ResearchTask(question="root")
    child = ResearchTask(question="child", dependencies=[root.id])
    graph = DAGTaskGraph([root, child])

    blocked = graph.mark_blocked_descendants(root.id)

    assert blocked == [child]
    assert child.status == TaskStatus.BLOCKED
