import pytest

from deepresearch_agent.agents import CriticAgent, PlannerAgent, ReaderAgent, SearcherAgent, VerifierAgent, WriterAgent
from deepresearch_agent.agents.searcher import SearchResult
from deepresearch_agent.redblue.blue_agent import BlueRepairAgent
from deepresearch_agent.schemas import Claim, Evidence, PlanType, ResearchReport, ResearchTask


@pytest.mark.asyncio
async def test_planner_searcher_reader_run_interfaces() -> None:
    task = ResearchTask(question="Why verify citations?")
    planner_result = await PlannerAgent().run(task.question)
    search_result = await SearcherAgent().run(task)

    assert planner_result.ok
    assert search_result.ok
    assert planner_result.output.tasks
    assert search_result.output

    reader_result = await ReaderAgent().run({"task": task, "results": search_result.output})

    assert reader_result.ok
    assert reader_result.output


@pytest.mark.asyncio
async def test_writer_verifier_critic_and_blue_run_interfaces() -> None:
    evidence = Evidence(
        task_id="task_a",
        source_id="source_a",
        title="Citation Verification",
        text="Citation verification links claims to inspectable evidence.",
        quote="Citation verification links claims to inspectable evidence.",
        url="local://citation",
        score=1.0,
    )
    writer_result = await WriterAgent().run(
        {
            "question": "Why verify citations?",
            "evidence": [evidence],
            "context": None,
            "plan_type": PlanType.RISK_ANALYSIS,
        }
    )

    assert writer_result.ok
    report = writer_result.output
    assert isinstance(report, ResearchReport)

    claim = Claim(text="Citation verification links claims to evidence.", citation_ids=[evidence.id])
    verifier_result = await VerifierAgent().run({"claim": claim, "evidence": [evidence]})

    assert verifier_result.ok
    verified = verifier_result.output
    assert verified.verification_trace is not None

    report.claims = [verified]
    critic_result = await CriticAgent().run(report)
    assert critic_result.ok

    blue_result = await BlueRepairAgent().run({"report": report, "findings": critic_result.output})
    assert blue_result.ok
    assert isinstance(blue_result.output, ResearchReport)


@pytest.mark.asyncio
async def test_agent_run_wraps_invalid_input_as_error() -> None:
    result = await SearcherAgent().run({"not": "a task"})

    assert not result.ok
    assert "ResearchTask" in result.error


def test_reader_run_test_uses_search_result_shape() -> None:
    result = SearchResult(
        source_id="source",
        title="title",
        snippet="snippet",
        url="local://source",
        score=1.0,
        text="snippet. second sentence.",
    )

    assert result.source_id == "source"
