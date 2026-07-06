import pytest

from deepresearch_agent.agents.searcher import SearcherAgent
from deepresearch_agent.schemas import ResearchTask


@pytest.mark.asyncio
async def test_searcher_expands_chinese_comparison_query() -> None:
    searcher = SearcherAgent()
    task = ResearchTask(question="比较 SQLite 和向量数据库的优缺点")

    results = await searcher.search(task)
    source_ids = {result.source_id for result in results}

    assert "sqlite_vector_tradeoffs" in source_ids
    assert {"sqlite_memory", "vector_retrieval", "hybrid_memory_design"} & source_ids
    assert results[0].hybrid_score >= results[-1].hybrid_score


def test_searcher_query_terms_include_expansions() -> None:
    searcher = SearcherAgent()
    terms = searcher._query_terms("比较 SQLite 和向量数据库的优缺点")

    assert "sqlite" in terms
    assert "vector" in terms
    assert "embedding" in terms
    assert "tradeoffs" in terms
