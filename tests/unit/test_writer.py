import pytest

from deepresearch_agent.agents.writer import WriterAgent
from deepresearch_agent.schemas import Evidence, PlanType


def _evidence(text: str, score: float = 1.0) -> Evidence:
    return Evidence(
        task_id="task_1",
        title=text,
        text=text,
        quote=text,
        source_id="source_1",
        chunk_id="chunk_1",
        score=score,
    )


@pytest.mark.asyncio
async def test_writer_uses_comparison_report_shape() -> None:
    writer = WriterAgent()
    evidence = [
        _evidence("SQLite memory helps reproducible debugging for runs, tasks, evidence, and claims."),
        _evidence("Vector embedding retrieval uses cosine similarity for semantic evidence reuse."),
    ]

    report = await writer.write(
        question="比较 SQLite 和向量数据库的优缺点",
        evidence=evidence,
        plan_type=PlanType.COMPARISON,
    )

    assert report.title == "DeepResearch Agent Comparison Report"
    assert [section.title for section in report.sections[:2]] == [
        "Comparison Frame",
        "Tradeoffs and Recommendation",
    ]
    assert "compares alternatives" in report.summary
    assert any("SQLite is strong" in claim.text for claim in report.claims)
    assert any("Vector retrieval" in claim.text for claim in report.claims)


@pytest.mark.asyncio
async def test_writer_uses_risk_report_shape() -> None:
    writer = WriterAgent()
    evidence = [
        _evidence("Hallucination detection checks unsupported claims, missing citations, and contradictions."),
        _evidence("A Red Agent attacks reports and a Blue Agent repairs them with ADD, DELETE, MODIFY, and VERIFY."),
    ]

    report = await writer.write(
        question="为什么 DeepResearch Agent 需要引用验证？",
        evidence=evidence,
        plan_type=PlanType.RISK_ANALYSIS,
    )

    assert report.title == "DeepResearch Agent Risk Analysis Report"
    assert [section.title for section in report.sections[:2]] == [
        "Failure Modes",
        "Mitigation and Verification",
    ]
    assert "failure modes" in report.summary
    assert any("not grounded" in claim.text for claim in report.claims)
    assert any("Red-Blue repair loops" in claim.text for claim in report.claims)


@pytest.mark.asyncio
async def test_writer_keeps_general_report_shape_by_default() -> None:
    writer = WriterAgent()
    report = await writer.write(
        question="test question",
        evidence=[_evidence("Citation evidence source chunk for verifier audit.")],
    )

    assert report.title == "DeepResearch Agent Offline Research Report"
    assert [section.title for section in report.sections[:2]] == [
        "System Design",
        "Reliability Mechanisms",
    ]
