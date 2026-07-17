import pytest

from deepresearch_agent.agents.reader import ReaderAgent
from deepresearch_agent.agents.searcher import SearchResult
from deepresearch_agent.schemas import ResearchTask


@pytest.mark.asyncio
async def test_reader_records_source_quality_metadata() -> None:
    task = ResearchTask(question="Why keep citation quotes?")
    result = SearchResult(
        source_id="source_quality",
        title="Citation Quality",
        snippet="Citation quotes keep verifier checks inspectable.",
        url="local://quality",
        score=1.5,
        text="Citation quotes keep verifier checks inspectable. They also help repair weak claims.",
        source_type="trust_note",
        trust_level="high",
    )

    evidence = await ReaderAgent().read(task, [result])

    assert evidence
    assert evidence[0].metadata["source_quality"] >= 0.75
    assert evidence[0].metadata["source_quality_band"] == "high"
    assert evidence[0].metadata["source_quality_signals"]["quote_in_text"] is True


@pytest.mark.asyncio
async def test_reader_keeps_pdf_page_locator_in_evidence() -> None:
    task = ResearchTask(question="What is the page-level evidence?")
    result = SearchResult(
        source_id="paper_01_p004_01",
        title="Page-aware Paper",
        snippet="Page-level citations are inspectable.",
        url="profile://paper/paper.pdf#page=4&chunk=1",
        score=1.0,
        text="Page-level citations are inspectable.",
        source_type="corpus_profile",
        trust_level="high",
        metadata={
            "page_number": 4,
            "page_start": 4,
            "page_end": 4,
            "citation_locator": "p. 4",
        },
    )

    evidence = await ReaderAgent().read(task, [result])

    assert evidence[0].chunk_id == "paper_01_p004_01#page-4-chunk-1"
    assert evidence[0].metadata["citation_locator"] == "p. 4"
