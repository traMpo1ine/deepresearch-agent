from __future__ import annotations

from pathlib import Path

import pytest

from deepresearch_agent.tools.web_search import (
    ArxivSearchProvider,
    CachedWebSearchProvider,
    CompositeWebSearchProvider,
    DirectURLProvider,
    FallbackSearchCache,
    GitHubSearchProvider,
    RedisSearchCache,
    ResilientWebSearchProvider,
    SQLiteSearchCache,
    WebSearchResult,
    create_web_search_provider,
    provider_telemetry,
    web_search_status,
)
from deepresearch_agent.tools.web_fetch import FetchedPage


class _CountingProvider:
    def __init__(self, provider_name: str = "fake", url: str = "https://example.com/a") -> None:
        self.calls = 0
        self.provider_name = provider_name
        self.url = url

    async def search(self, query: str, max_results: int = 3) -> list[WebSearchResult]:
        self.calls += 1
        return [
            WebSearchResult(
                title=f"{self.provider_name} result",
                url=self.url,
                content=f"Full text for {query}",
                provider=self.provider_name,
            )
        ]


@pytest.mark.asyncio
async def test_sqlite_search_cache_avoids_duplicate_provider_calls(tmp_path: Path) -> None:
    source = _CountingProvider()
    provider = CachedWebSearchProvider(
        source,
        SQLiteSearchCache(tmp_path / "web.sqlite3", ttl_seconds=3600),
        provider_name="fake",
    )

    first = await provider.search("agent evaluation", max_results=2)
    second = await provider.search("agent evaluation", max_results=2)

    assert first[0].url == second[0].url
    assert first[0].content == second[0].content
    assert source.calls == 1
    assert first[0].metadata.get("cache_hit", False) is False
    assert second[0].metadata["cache_hit"] is True


@pytest.mark.asyncio
async def test_composite_provider_deduplicates_urls() -> None:
    provider = CompositeWebSearchProvider(
        [
            _CountingProvider("one", "https://example.com/shared"),
            _CountingProvider("two", "https://example.com/shared/"),
        ]
    )

    results = await provider.search("same source", max_results=3)

    assert len(results) == 1
    assert results[0].provider == "one"


@pytest.mark.asyncio
async def test_composite_provider_round_robins_distinct_sources() -> None:
    provider = CompositeWebSearchProvider(
        [
            _CountingProvider("one", "https://example.com/one"),
            _CountingProvider("two", "https://example.com/two"),
        ]
    )

    results = await provider.search("multi source", max_results=2)

    assert [result.provider for result in results] == ["one", "two"]


@pytest.mark.asyncio
async def test_resilient_provider_retries_and_records_telemetry() -> None:
    class _FlakyProvider:
        def __init__(self) -> None:
            self.calls = 0

        async def search(self, query: str, max_results: int = 3) -> list[WebSearchResult]:
            self.calls += 1
            if self.calls == 1:
                raise ConnectionError("temporary outage")
            return [WebSearchResult(title="ok", url="https://example.com", content=query)]

    source = _FlakyProvider()
    provider = ResilientWebSearchProvider(
        source,
        "flaky",
        max_retries=1,
        min_interval_seconds=0,
    )

    results = await provider.search("agent reliability", max_results=1)
    telemetry = provider_telemetry(provider)

    assert source.calls == 2
    assert results[0].metadata["provider_attempts"] == 2
    assert results[0].metadata["provider_retries"] == 1
    assert telemetry["summary"]["total_retries"] == 1
    assert telemetry["events"][0]["status"] == "success"


@pytest.mark.asyncio
async def test_resilient_provider_opens_circuit_after_repeated_failures() -> None:
    class _FailingProvider:
        def __init__(self) -> None:
            self.calls = 0

        async def search(self, query: str, max_results: int = 3) -> list[WebSearchResult]:
            self.calls += 1
            raise ConnectionError("provider down")

    source = _FailingProvider()
    provider = ResilientWebSearchProvider(
        source,
        "failing",
        max_retries=0,
        failure_threshold=2,
        reset_seconds=60,
    )

    assert await provider.search("one") == []
    assert await provider.search("two") == []
    assert await provider.search("three") == []
    telemetry = provider_telemetry(provider)

    assert source.calls == 2
    assert telemetry["summary"]["circuit_open_count"] == 1
    assert telemetry["events"][-1]["status"] == "circuit_open"
    assert telemetry["events"][-1]["attempts"] == 0


def test_provider_factory_and_status_support_multi_source(tmp_path: Path) -> None:
    provider = create_web_search_provider(
        "tavily,wikipedia,searxng",
        cache_path=tmp_path / "cache.sqlite3",
    )
    status = web_search_status("tavily,wikipedia,searxng")

    assert isinstance(provider, CachedWebSearchProvider)
    assert [item["provider"] for item in status["providers"]] == [
        "tavily",
        "wikipedia",
        "searxng",
    ]
    assert status["env_configured"] is True


@pytest.mark.asyncio
async def test_arxiv_provider_parses_real_source_shape(monkeypatch) -> None:
    payload = b"""<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/2401.00001v1</id>
        <updated>2024-01-01T00:00:00Z</updated>
        <published>2024-01-01T00:00:00Z</published>
        <title>Retrieval Augmented Generation</title>
        <summary>A grounded generation method with external evidence.</summary>
      </entry>
    </feed>"""
    monkeypatch.setattr(
        "deepresearch_agent.tools.web_search._request_bytes",
        lambda *args, **kwargs: payload,
    )

    results = await ArxivSearchProvider().search("retrieval augmented generation", max_results=1)

    assert results[0].source_type == "academic_paper"
    assert results[0].url.startswith("https://arxiv.org/")
    assert results[0].metadata["content_origin"] == "arxiv_abstract"
    assert len(results[0].metadata["content_sha256"]) == 64


@pytest.mark.asyncio
async def test_github_provider_uses_readme_and_repository_metadata(monkeypatch) -> None:
    monkeypatch.setattr(
        "deepresearch_agent.tools.web_search._request_json",
        lambda *args, **kwargs: {
            "items": [
                {
                    "full_name": "org/deep-research",
                    "html_url": "https://github.com/org/deep-research",
                    "description": "Research agent",
                    "language": "Python",
                    "stargazers_count": 42,
                    "forks_count": 5,
                    "topics": ["agent"],
                    "updated_at": "2026-07-01T00:00:00Z",
                }
            ]
        },
    )
    monkeypatch.setattr(
        "deepresearch_agent.tools.web_search._request_text",
        lambda *args, **kwargs: "# Deep Research\nReal README content.",
    )

    results = await GitHubSearchProvider().search("deep research agent", max_results=1)

    assert results[0].source_type == "code_repository"
    assert results[0].metadata["content_origin"] == "github_readme"
    assert results[0].metadata["language"] == "Python"
    assert results[0].metadata["stars"] == 42


@pytest.mark.asyncio
async def test_direct_url_provider_reads_embedded_public_url() -> None:
    class _FakeFetcher:
        async def fetch(self, url: str) -> FetchedPage:
            return FetchedPage(
                url=url,
                final_url=url,
                text="Full HTML or PDF text with inspectable evidence.",
                status="ok",
                content_type="text/html",
                fetched_at="2026-07-16T00:00:00+00:00",
                content_sha256="b" * 64,
                bytes_read=100,
            )

    results = await DirectURLProvider(fetcher=_FakeFetcher()).search(
        "Read https://example.com/report.pdf and summarize it.", max_results=1
    )

    assert results[0].url == "https://example.com/report.pdf"
    assert results[0].source_type == "web_page"
    assert results[0].metadata["content_origin"] == "direct_url_fetch"


def test_redis_search_cache_serializes_ttl_results() -> None:
    class _FakeRedis:
        def __init__(self) -> None:
            self.values = {}
            self.ttl = None

        def get(self, key):
            return self.values.get(key)

        def setex(self, key, ttl, value):
            self.values[key] = value
            self.ttl = ttl

    client = _FakeRedis()
    cache = RedisSearchCache(ttl_seconds=120, client=client)
    expected = [WebSearchResult(title="Redis", url="https://example.com", content="cached")]

    cache.put("fake", "query", 1, expected)
    actual = cache.get("fake", "query", 1)

    assert client.ttl == 120
    assert actual is not None
    assert actual[0].content == "cached"
    assert actual[0].metadata["cache_backend"] == "redis"


def test_redis_cache_falls_back_to_sqlite(tmp_path: Path) -> None:
    class _FailingCache:
        backend_name = "redis"

        def get(self, *args, **kwargs):
            raise ConnectionError("redis unavailable")

        def put(self, *args, **kwargs):
            raise ConnectionError("redis unavailable")

    fallback = SQLiteSearchCache(tmp_path / "fallback.sqlite3")
    cache = FallbackSearchCache(_FailingCache(), fallback)
    expected = [WebSearchResult(title="Fallback", url="https://example.com", content="ok")]

    cache.put("fake", "query", 1, expected)
    actual = cache.get("fake", "query", 1)

    assert actual is not None
    assert actual[0].metadata["cache_backend"] == "sqlite"
    assert actual[0].metadata["cache_fallback_from"] == "redis"
