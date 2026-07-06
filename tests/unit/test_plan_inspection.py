import pytest

from deepresearch_agent.agents.planner import PlannerAgent
from deepresearch_agent.orchestration.inspection import plan_overview, plan_to_markdown


@pytest.mark.asyncio
async def test_plan_inspection_exposes_batches_and_mermaid() -> None:
    plan = await PlannerAgent().plan("Why does DeepResearch need citation verification?")

    overview = plan_overview(plan)
    markdown = plan_to_markdown(plan)

    assert overview["task_count"] >= 5
    assert len(overview["topological_batches"]) >= 3
    assert "flowchart TD" in overview["mermaid"]
    assert "Topological Batches" in markdown
