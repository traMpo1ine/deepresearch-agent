import pytest

from deepresearch_agent.agents.writer import WriterAgent
from deepresearch_agent.llm import LLMMessage
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


class _FakeGroundedBackend:
    async def complete(self, messages: list[LLMMessage]) -> str:
        return "unused"

    async def structured_complete(self, messages: list[LLMMessage]) -> dict:
        assert "untrusted data" in messages[0].content
        return {
            "title": "Grounded answer",
            "summary": "A source-grounded summary.",
            "claims": [
                {
                    "text": "The public source describes a concrete control.",
                    "citation_ids": ["live_1"],
                },
                {
                    "text": "This invalid citation must be discarded.",
                    "citation_ids": ["invented_id"],
                },
            ],
            "limitations": ["One controlled source set was used."],
        }

    async def embed(self, text: str) -> list[float]:
        return [1.0]


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


@pytest.mark.asyncio
async def test_extractive_writer_prefers_distinct_live_sources() -> None:
    evidence = [
        Evidence(
            id=f"live_{index}",
            task_id="task_1",
            title=f"Public source {index}",
            text=f"Inspectable statement from public source {index}.",
            quote=f"Inspectable statement from public source {index}.",
            url=f"https://example{index}.org/source",
            source_id=f"public_{index}",
            score=0.8,
        )
        for index in range(1, 4)
    ]
    evidence.append(_evidence("Higher-scored local template evidence.", score=2.0))

    report = await WriterAgent(mode="extractive").write(
        question="Use real sources",
        evidence=evidence,
    )

    assert len(report.claims) == 3
    assert {claim.citation_ids[0] for claim in report.claims} == {
        "live_1",
        "live_2",
        "live_3",
    }
    assert all("public source" in claim.text for claim in report.claims)


@pytest.mark.asyncio
async def test_extractive_writer_prefers_substantive_chunk_over_navigation() -> None:
    evidence = [
        Evidence(
            id="nav",
            task_id="task_1",
            title="Public source",
            text="Skip to main content. Register now. Press Enter to search.",
            quote="Skip to main content. Register now. Press Enter to search.",
            url="https://example.org/source",
            source_id="public_1",
            score=1.0,
        ),
        Evidence(
            id="substantive",
            task_id="task_1",
            title="Public source",
            text=(
                "The evaluation examines retrieval relevance, answer accuracy, "
                "and faithfulness as separate signals."
            ),
            quote=(
                "The evaluation examines retrieval relevance, answer accuracy, "
                "and faithfulness as separate signals."
            ),
            url="https://example.org/source",
            source_id="public_1",
            score=0.8,
        ),
    ]

    report = await WriterAgent(mode="extractive").write("Evaluate RAG", evidence=evidence)

    assert report.claims[0].citation_ids == ["substantive"]
    assert "faithfulness" in report.claims[0].text


@pytest.mark.asyncio
async def test_llm_writer_accepts_only_supplied_citation_ids() -> None:
    evidence = [
        Evidence(
            id="live_1",
            task_id="task_1",
            title="Public source",
            text="A concrete control is documented.",
            quote="A concrete control is documented.",
            url="https://example.org/source",
            source_id="public_1",
            score=0.8,
        )
    ]

    report = await WriterAgent(mode="llm", llm_backend=_FakeGroundedBackend()).write(
        question="What control is documented?",
        evidence=evidence,
    )

    assert report.title == "Grounded answer"
    assert len(report.claims) == 1
    assert report.claims[0].citation_ids == ["live_1"]
    assert report.limitations[1] == "One controlled source set was used."
