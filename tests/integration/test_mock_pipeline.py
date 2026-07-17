import pytest

from deepresearch_agent.agents.base import AgentContext, BaseAgent
from deepresearch_agent.orchestration.coordinator import ResearchCoordinator
from deepresearch_agent.schemas import ResearchPlan, ResearchTask, TaskStatus, TaskType


class _TinyPlanner(BaseAgent):
    name = "planner"

    async def _run(self, agent_input: object, context: AgentContext | None = None) -> ResearchPlan:
        root = ResearchTask(question=str(agent_input), task_type=TaskType.ROOT)
        search = ResearchTask(
            question="slow search",
            task_type=TaskType.SEARCH,
            dependencies=[root.id],
            timeout_seconds=0.001,
            max_retries=0,
        )
        synthesize = ResearchTask(
            question="synthesize",
            task_type=TaskType.SYNTHESIZE,
            dependencies=[search.id],
        )
        verify = ResearchTask(
            question="verify",
            task_type=TaskType.VERIFY,
            dependencies=[synthesize.id],
        )
        repair = ResearchTask(
            question="repair",
            task_type=TaskType.REPAIR,
            dependencies=[verify.id],
        )
        return ResearchPlan(
            root_question=str(agent_input),
            tasks=[root, search, synthesize, verify, repair],
            rationale="Tiny timeout plan for failure inspection.",
        )


class _SlowSearcher(BaseAgent):
    name = "searcher"

    async def _run(self, agent_input: object, context: AgentContext | None = None) -> list:
        import asyncio

        await asyncio.sleep(0.01)
        return []


@pytest.mark.asyncio
async def test_mock_pipeline_generates_report(tmp_path) -> None:
    coordinator = ResearchCoordinator(
        max_concurrency=2,
        memory_path=tmp_path / "memory.sqlite3",
        vector_path=tmp_path / "vector_index.npz",
        plan_dir=tmp_path / "plans",
    )

    report = await coordinator.run("Why should deep research agents verify citations?")

    assert report.claims
    assert report.evidence
    assert "DeepResearch Agent" in report.title
    assert report.run_summary["task_count"] >= 5
    assert (tmp_path / "vector_index.npz").exists()
    event_names = {event["agent_name"] for event in coordinator.memory.list_agent_events(report.run_id)}
    assert {"planner", "searcher", "reader", "writer", "verifier"}.issubset(event_names)


@pytest.mark.asyncio
async def test_corrupted_vector_index_is_rebuilt(tmp_path) -> None:
    vector_path = tmp_path / "vector_index.npz"
    vector_path.write_text("not a valid npz", encoding="utf-8")
    with pytest.warns(RuntimeWarning, match="rebuilding an empty index"):
        coordinator = ResearchCoordinator(
            max_concurrency=2,
            memory_path=tmp_path / "memory.sqlite3",
            vector_path=vector_path,
            plan_dir=tmp_path / "plans",
        )

    report = await coordinator.run("Why does the agent need reproducible memory?")

    assert report.evidence


@pytest.mark.asyncio
async def test_timeout_replan_and_fallback_are_recorded(tmp_path) -> None:
    coordinator = ResearchCoordinator(
        max_concurrency=1,
        memory_path=tmp_path / "memory.sqlite3",
        vector_path=tmp_path / "vector_index.npz",
        plan_dir=tmp_path / "plans",
        min_evidence_count=1,
        batch_replan_threshold=1,
    )
    coordinator.planner = _TinyPlanner()
    coordinator.searcher = _SlowSearcher()

    report = await coordinator.run("trigger timeout")

    assert report.run_summary["fallback_level"] == 3
    assert report.run_summary["replan_count"] >= 1
    assert report.run_summary["timed_out_tasks"] >= 1
    assert report.run_summary["batch_failure_events"]
    assert any("Fallback synthesis" in item for item in report.limitations)
    task_rows = coordinator.memory.list_tasks(report.run_id)
    assert any(row["status"] == TaskStatus.FAILED.value for row in task_rows)


@pytest.mark.asyncio
async def test_evidence_threshold_fallback_keeps_report_readable(tmp_path) -> None:
    coordinator = ResearchCoordinator(
        max_concurrency=2,
        memory_path=tmp_path / "memory.sqlite3",
        vector_path=tmp_path / "vector_index.npz",
        plan_dir=tmp_path / "plans",
        min_evidence_count=999,
    )

    report = await coordinator.run("Why should fallback reports disclose evidence limits?")

    assert report.claims
    assert report.run_summary["fallback_level"] == 3
    assert any("Fallback synthesis" in item for item in report.limitations)


@pytest.mark.asyncio
async def test_iterative_search_records_follow_up_trace(tmp_path) -> None:
    coordinator = ResearchCoordinator(
        max_concurrency=2,
        memory_path=tmp_path / "memory.sqlite3",
        vector_path=tmp_path / "vector_index.npz",
        plan_dir=tmp_path / "plans",
        use_iterative_search=True,
        source_quality_threshold=1.1,
        max_follow_up_queries=1,
    )

    report = await coordinator.run("Why should deep research agents preserve citation quotes?")

    assert report.run_summary["iterative_search_enabled"] is True
    assert report.run_summary["follow_up_query_count"] == 1
    assert report.run_summary["follow_up_queries"]
    assert "source_quality" in report.run_summary
    assert report.run_summary["source_quality"]["evidence_count"] == report.run_summary["evidence_count"]
