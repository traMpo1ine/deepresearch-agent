import pytest

from deepresearch_agent.agents.searcher import SearcherAgent
from deepresearch_agent.schemas import ResearchTask
from deepresearch_agent.tools.web_search import TavilySearchProvider, WebSearchResult, web_search_status


class _FakeWebSearchProvider:
    async def search(self, query: str, max_results: int = 3) -> list[WebSearchResult]:
        return [
            WebSearchResult(
                title="Web citation source",
                url="https://example.com/citation",
                content="Citation verification benefits from web search evidence and exact quotes.",
                score=0.9,
                provider="fake",
            )
        ]


class _FakeEmbeddingProvider:
    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] if "citation" in text.lower() else [0.0, 1.0] for text in texts]

    def status(self) -> dict[str, object]:
        return {"provider": "fake", "env_configured": True}


@pytest.mark.asyncio
async def test_searcher_expands_chinese_comparison_query() -> None:
    searcher = SearcherAgent()
    task = ResearchTask(question="比较 SQLite 和向量数据库的优缺点")

    results = await searcher.search(task)
    source_ids = {result.source_id for result in results}

    assert "sqlite_vector_tradeoffs" in source_ids
    assert {"sqlite_memory", "vector_retrieval", "hybrid_memory_design"} & source_ids
    assert results[0].hybrid_score >= results[-1].hybrid_score


@pytest.mark.asyncio
async def test_searcher_can_use_async_embedding_provider(tmp_path) -> None:
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(
        "\n".join(
            [
                '{"id":"citation","title":"Citation","text":"claim evidence",'
                '"url":"local://citation"}',
                '{"id":"cooking","title":"Cooking","text":"soup recipe",'
                '"url":"local://cooking"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    searcher = SearcherAgent(
        corpus_path=corpus,
        retrieval_mode="vector",
        result_limit=1,
        embedding_provider=_FakeEmbeddingProvider(),
    )

    results = await searcher.search(ResearchTask(question="citation verification"))

    assert results[0].source_id == "citation"
    assert searcher.embedding_telemetry()["provider"] == "fake"


def test_searcher_query_terms_include_expansions() -> None:
    searcher = SearcherAgent()
    terms = searcher._query_terms("比较 SQLite 和向量数据库的优缺点")

    assert "sqlite" in terms
    assert "vector" in terms
    assert "embedding" in terms
    assert "tradeoffs" in terms


def test_searcher_removes_planner_scaffolding_from_web_query() -> None:
    searcher = SearcherAgent()

    query = searcher._web_query(
        "Establish the background concepts and scope for: Deep Research 系统为什么需要引用验证？"
    )

    assert query == "Deep Research"


def test_searcher_preserves_explicit_urls_in_web_query() -> None:
    searcher = SearcherAgent()
    question = (
        "请基于这些资料回答为什么要验证："
        "https://www.nist.gov/example https://genai.owasp.org/example"
    )

    assert searcher._web_query(question) == question


@pytest.mark.asyncio
async def test_searcher_can_include_optional_web_results() -> None:
    searcher = SearcherAgent(
        corpus_path="data/corpus/does_not_exist.jsonl",
        enable_web_search=True,
        web_search_provider="disabled",
        provider=_FakeWebSearchProvider(),
    )
    task = ResearchTask(question="Why does citation verification need web search evidence?")

    results = await searcher.search(task)

    assert any(result.source_type == "web_search" for result in results)
    assert any(result.url == "https://example.com/citation" for result in results)


@pytest.mark.asyncio
async def test_searcher_preserves_source_diversity_with_local_corpus() -> None:
    searcher = SearcherAgent(
        enable_web_search=True,
        provider=_FakeWebSearchProvider(),
    )

    results = await searcher.search(
        ResearchTask(question="Why does citation verification need web search evidence?")
    )

    assert any(result.url == "https://example.com/citation" for result in results)
    assert any(result.url.startswith("local://") for result in results)


@pytest.mark.asyncio
async def test_tavily_provider_is_safe_when_unconfigured(monkeypatch) -> None:
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    assert web_search_status("tavily")["env_configured"] is False
    assert await TavilySearchProvider().search("test", max_results=1) == []
