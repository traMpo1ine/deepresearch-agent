import pytest

from deepresearch_agent.agents.planner import PlannerAgent
from deepresearch_agent.orchestration.dag import DAGTaskGraph
from deepresearch_agent.schemas import PlanType, TaskType


@pytest.mark.asyncio
async def test_planner_outputs_quality_report() -> None:
    plan = await PlannerAgent().plan("How should a DeepResearch Agent be evaluated?")

    assert len(plan.tasks) >= 5
    assert plan.quality_report is not None
    assert plan.quality_report.passed
    assert plan.quality_report.has_evaluation


@pytest.mark.asyncio
async def test_template_planner_keeps_stable_baseline_shape() -> None:
    planner = PlannerAgent(mode="template")

    first = await planner.plan("Why does DeepResearch need citation verification?")
    second = await planner.plan("Compare SQLite and vector databases.")

    assert first.plan_type == PlanType.GENERAL
    assert second.plan_type == PlanType.GENERAL
    assert len(first.tasks) == len(second.tasks) == 9
    assert len(DAGTaskGraph(first.tasks).topological_batches()) == 5
    assert len(DAGTaskGraph(second.tasks).topological_batches()) == 5


@pytest.mark.asyncio
async def test_heuristic_planner_changes_shape_for_comparison_and_risk() -> None:
    planner = PlannerAgent(mode="heuristic")

    comparison = await planner.plan("比较 SQLite 和向量数据库的优缺点")
    risk = await planner.plan("为什么 DeepResearch 需要引用验证？")

    comparison_batches = DAGTaskGraph(comparison.tasks).topological_batches()
    risk_batches = DAGTaskGraph(risk.tasks).topological_batches()
    assert comparison.plan_type == PlanType.COMPARISON
    assert risk.plan_type == PlanType.RISK_ANALYSIS
    assert len(comparison.tasks) == 8
    assert len(risk.tasks) == 9
    assert len(comparison_batches) != len(risk_batches)
    assert comparison.quality_report is not None and comparison.quality_report.passed
    assert risk.quality_report is not None and risk.quality_report.passed
    assert any(
        len(task.dependencies) > 1
        for task in comparison.tasks
        if task.task_type == TaskType.SEARCH
    )


def test_planner_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError, match="Unknown planner mode"):
        PlannerAgent(mode="unknown")
