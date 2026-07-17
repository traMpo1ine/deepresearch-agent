from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from deepresearch_agent.tools.web_fetch import FetchedPage, WebPageFetcher


USER_AGENT = "deepresearch-agent/0.1 (+https://github.com/traMpo1ine/deepresearch-agent)"


@dataclass(slots=True)
class WebSearchResult:
    title: str
    url: str
    content: str
    score: float = 0.0
    provider: str = "web"
    source_type: str = "web_search"
    trust_level: str = "medium"
    metadata: dict[str, object] = field(default_factory=dict)


class WebSearchProvider(Protocol):
    async def search(self, query: str, max_results: int = 3) -> list[WebSearchResult]:
        ...


class ProviderRequestError(RuntimeError):
    """Normalized transport/parsing failure for provider circuit breakers."""


@dataclass(slots=True)
class ProviderTelemetryEvent:
    provider: str
    query_preview: str
    query_sha256: str
    status: str
    result_count: int
    latency_seconds: float
    attempts: int
    retries: int
    circuit_state: str
    error_type: str | None
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class ResilientWebSearchProvider:
    """Provider wrapper with concurrency limits, retry, timeout, circuit breaker and telemetry."""

    def __init__(
        self,
        provider: WebSearchProvider,
        provider_name: str,
        *,
        timeout_seconds: float = 25.0,
        max_retries: int = 1,
        failure_threshold: int = 3,
        reset_seconds: float = 30.0,
        max_concurrency: int = 2,
        min_interval_seconds: float = 0.0,
    ) -> None:
        self.provider = provider
        self.provider_name = provider_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max(0, max_retries)
        self.failure_threshold = max(1, failure_threshold)
        self.reset_seconds = max(0.1, reset_seconds)
        self.min_interval_seconds = max(0.0, min_interval_seconds)
        self._semaphore = asyncio.Semaphore(max(1, max_concurrency))
        self._rate_lock = asyncio.Lock()
        self._last_started = 0.0
        self._consecutive_failures = 0
        self._circuit_state = "closed"
        self._opened_at = 0.0
        self._events: list[ProviderTelemetryEvent] = []

    async def search(self, query: str, max_results: int = 3) -> list[WebSearchResult]:
        started = time.perf_counter()
        if self._circuit_state == "open":
            if time.monotonic() - self._opened_at < self.reset_seconds:
                self._record(query, "circuit_open", 0, started, 0, None)
                return []
            self._circuit_state = "half_open"

        attempts = 0
        error_type: str | None = None
        status = "error"
        results: list[WebSearchResult] = []
        async with self._semaphore:
            await self._throttle()
            for attempt in range(self.max_retries + 1):
                attempts = attempt + 1
                try:
                    results = await asyncio.wait_for(
                        self.provider.search(query, max_results=max_results),
                        timeout=self.timeout_seconds,
                    )
                    status = "success" if results else "empty"
                    error_type = None
                    break
                except TimeoutError:
                    status = "timeout"
                    error_type = "TimeoutError"
                except Exception as exc:  # noqa: BLE001 - normalized into telemetry.
                    status = "error"
                    error_type = type(exc).__name__
                if attempt < self.max_retries:
                    await asyncio.sleep(0.25 * (2**attempt))

        if status in {"success", "empty"}:
            self._consecutive_failures = 0
            self._circuit_state = "closed"
        elif status in {"error", "timeout"}:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self.failure_threshold:
                self._circuit_state = "open"
                self._opened_at = time.monotonic()
        event = self._record(query, status, len(results), started, attempts, error_type)
        for result in results:
            result.metadata.update(
                {
                    "provider_attempts": event.attempts,
                    "provider_retries": event.retries,
                    "provider_latency_seconds": event.latency_seconds,
                    "provider_circuit_state": event.circuit_state,
                }
            )
        return results

    def telemetry_snapshot(self) -> list[dict[str, object]]:
        return [event.to_dict() for event in self._events]

    async def _throttle(self) -> None:
        if self.min_interval_seconds <= 0:
            return
        async with self._rate_lock:
            delay = self.min_interval_seconds - (time.monotonic() - self._last_started)
            if delay > 0:
                await asyncio.sleep(delay)
            self._last_started = time.monotonic()

    def _record(
        self,
        query: str,
        status: str,
        result_count: int,
        started: float,
        attempts: int,
        error_type: str | None,
    ) -> ProviderTelemetryEvent:
        event = ProviderTelemetryEvent(
            provider=self.provider_name,
            query_preview=" ".join(query.split())[:120],
            query_sha256=hashlib.sha256(query.encode("utf-8")).hexdigest(),
            status=status,
            result_count=result_count,
            latency_seconds=round(time.perf_counter() - started, 4),
            attempts=attempts,
            retries=max(0, attempts - 1),
            circuit_state=self._circuit_state,
            error_type=error_type,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._events.append(event)
        if len(self._events) > 200:
            del self._events[:-200]
        return event


class SearchCache(Protocol):
    backend_name: str

    def get(self, provider: str, query: str, max_results: int) -> list[WebSearchResult] | None:
        ...

    def put(
        self,
        provider: str,
        query: str,
        max_results: int,
        results: list[WebSearchResult],
    ) -> None:
        ...


class DisabledWebSearchProvider:
    async def search(self, query: str, max_results: int = 3) -> list[WebSearchResult]:
        return []


class TavilySearchProvider:
    name = "tavily"

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str = "https://api.tavily.com/search",
        timeout_seconds: float = 20.0,
    ) -> None:
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def search(self, query: str, max_results: int = 3) -> list[WebSearchResult]:
        if not self.configured:
            return []
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "include_answer": False,
            # Deep research needs page text, not only search snippets.
            "include_raw_content": True,
        }
        raw = await asyncio.to_thread(
            _request_json,
            self.endpoint,
            payload,
            self.timeout_seconds,
        )
        if not raw:
            return []
        results = raw.get("results", [])
        if not isinstance(results, list):
            return []
        parsed: list[WebSearchResult] = []
        for item in results[:max_results]:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or item.get("url") or "Untitled web result")
            url = str(item.get("url") or "")
            raw_content = item.get("raw_content")
            content = str(raw_content or item.get("content") or item.get("snippet") or "")
            if not url or not content:
                continue
            parsed.append(
                WebSearchResult(
                    title=title,
                    url=url,
                    content=content,
                    score=float(item.get("score") or 0.0),
                    provider=self.name,
                    metadata=_lineage_metadata(
                        content,
                        content_origin="tavily_raw_content" if raw_content else "tavily_snippet",
                        fetch_status="provider_content",
                    ),
                )
            )
        return parsed


class WikipediaSearchProvider:
    """Keyless MediaWiki search with article extracts as citable source text."""

    name = "wikipedia"

    def __init__(
        self,
        language: str | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        self.language = language or os.getenv("WIKIPEDIA_LANGUAGE", "zh")
        self.timeout_seconds = timeout_seconds

    async def search(self, query: str, max_results: int = 3) -> list[WebSearchResult]:
        endpoint = f"https://{self.language}.wikipedia.org/w/api.php"
        params = urllib.parse.urlencode(
            {
                "action": "query",
                "generator": "search",
                "gsrsearch": query,
                "gsrlimit": max_results,
                "prop": "extracts|info",
                "inprop": "url",
                "explaintext": 1,
                "exintro": 1,
                "redirects": 1,
                "format": "json",
                "formatversion": 2,
                "utf8": 1,
            }
        )
        raw = await asyncio.to_thread(
            _request_json,
            f"{endpoint}?{params}",
            None,
            self.timeout_seconds,
        )
        if not raw:
            return []
        pages = raw.get("query", {}).get("pages", [])
        if not isinstance(pages, list):
            return []
        parsed: list[WebSearchResult] = []
        for rank, page in enumerate(pages[:max_results], start=1):
            if not isinstance(page, dict):
                continue
            title = str(page.get("title") or "")
            url = str(page.get("fullurl") or "")
            content = str(page.get("extract") or "")
            if not title or not url or not content:
                continue
            parsed.append(
                WebSearchResult(
                    title=title,
                    url=url,
                    content=content,
                    score=max(0.0, 1.0 - (rank - 1) * 0.1),
                    provider=self.name,
                    source_type="encyclopedia",
                    trust_level="high",
                    metadata=_lineage_metadata(
                        content,
                        content_origin="mediawiki_extract",
                        fetch_status="provider_content",
                    ),
                )
            )
        return parsed


class ArxivSearchProvider:
    """Keyless arXiv Atom API adapter for academic-paper abstracts."""

    name = "arxiv"

    def __init__(
        self,
        endpoint: str = "https://export.arxiv.org/api/query",
        timeout_seconds: float = 20.0,
    ) -> None:
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    async def search(self, query: str, max_results: int = 3) -> list[WebSearchResult]:
        params = urllib.parse.urlencode(
            {
                "search_query": f'all:"{query}"',
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending",
            }
        )
        payload = await asyncio.to_thread(
            _request_bytes,
            f"{self.endpoint}?{params}",
            self.timeout_seconds,
        )
        if not payload:
            return []
        try:
            root = ET.fromstring(payload)
        except ET.ParseError:
            return []
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        results: list[WebSearchResult] = []
        for rank, entry in enumerate(root.findall("atom:entry", namespace), start=1):
            title = _collapse_whitespace(entry.findtext("atom:title", "", namespace))
            abstract = _collapse_whitespace(entry.findtext("atom:summary", "", namespace))
            paper_id = entry.findtext("atom:id", "", namespace).strip()
            published = entry.findtext("atom:published", "", namespace).strip()
            updated = entry.findtext("atom:updated", "", namespace).strip()
            url = paper_id.replace("http://", "https://")
            if not title or not abstract or not url:
                continue
            results.append(
                WebSearchResult(
                    title=title,
                    url=url,
                    content=abstract,
                    score=max(0.0, 1.0 - (rank - 1) * 0.1),
                    provider=self.name,
                    source_type="academic_paper",
                    trust_level="high",
                    metadata={
                        **_lineage_metadata(
                            abstract,
                            content_origin="arxiv_abstract",
                            fetch_status="provider_content",
                        ),
                        "published_at": published,
                        "updated_at": updated,
                    },
                )
            )
        return results[:max_results]


class GitHubSearchProvider:
    """GitHub repository search plus README retrieval through the official API."""

    name = "github"

    def __init__(self, token: str | None = None, timeout_seconds: float = 20.0) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.timeout_seconds = timeout_seconds

    @property
    def headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def search(self, query: str, max_results: int = 3) -> list[WebSearchResult]:
        params = urllib.parse.urlencode(
            {"q": query, "sort": "stars", "order": "desc", "per_page": max_results}
        )
        raw = await asyncio.to_thread(
            _request_json,
            f"https://api.github.com/search/repositories?{params}",
            None,
            self.timeout_seconds,
            self.headers,
        )
        if not raw:
            return []
        items = raw.get("items", [])
        if not isinstance(items, list):
            return []
        readmes = await asyncio.gather(
            *(self._readme(str(item.get("full_name") or "")) for item in items[:max_results]),
            return_exceptions=True,
        )
        results: list[WebSearchResult] = []
        for rank, (item, readme) in enumerate(zip(items[:max_results], readmes, strict=False), start=1):
            if not isinstance(item, dict):
                continue
            full_name = str(item.get("full_name") or "")
            url = str(item.get("html_url") or "")
            if not full_name or not url:
                continue
            metadata_text = "\n".join(
                [
                    f"Repository: {full_name}",
                    f"Description: {item.get('description') or 'No description'}",
                    f"Language: {item.get('language') or 'Unknown'}",
                    f"Stars: {int(item.get('stargazers_count') or 0)}",
                    f"Forks: {int(item.get('forks_count') or 0)}",
                    f"Topics: {', '.join(item.get('topics') or [])}",
                    f"Updated at: {item.get('updated_at') or ''}",
                ]
            )
            readme_text = readme if isinstance(readme, str) else ""
            content = readme_text or metadata_text
            results.append(
                WebSearchResult(
                    title=full_name,
                    url=url,
                    content=content,
                    score=max(0.0, 1.0 - (rank - 1) * 0.1),
                    provider=self.name,
                    source_type="code_repository",
                    trust_level="medium",
                    metadata={
                        **_lineage_metadata(
                            content,
                            content_origin=(
                                "github_readme" if readme_text else "github_repository_metadata"
                            ),
                            fetch_status="provider_content",
                        ),
                        "repository": full_name,
                        "language": item.get("language"),
                        "stars": int(item.get("stargazers_count") or 0),
                        "forks": int(item.get("forks_count") or 0),
                        "updated_at": item.get("updated_at"),
                    },
                )
            )
        return results

    async def _readme(self, full_name: str) -> str:
        if not full_name:
            return ""
        headers = {**self.headers, "Accept": "application/vnd.github.raw+json"}
        try:
            return await asyncio.to_thread(
                _request_text,
                f"https://api.github.com/repos/{full_name}/readme",
                self.timeout_seconds,
                headers,
            )
        except ProviderRequestError:
            # A repository without a readable README is still a valid search result.
            return ""


class DirectURLProvider:
    """Read public HTML/PDF/text URLs embedded directly in the research question."""

    name = "url"
    URL_PATTERN = re.compile(r"https?://[^\s<>\]\[\"']+")

    def __init__(self, fetcher: WebPageFetcher | None = None) -> None:
        self.fetcher = fetcher or WebPageFetcher()

    async def search(self, query: str, max_results: int = 3) -> list[WebSearchResult]:
        urls = []
        for match in self.URL_PATTERN.findall(query):
            url = match.rstrip(".,;:!?。；，！？)")
            if url not in urls:
                urls.append(url)
        pages = await asyncio.gather(
            *(self.fetcher.fetch(url) for url in urls[:max_results]),
            return_exceptions=True,
        )
        results = []
        for url, page in zip(urls, pages, strict=False):
            if isinstance(page, BaseException) or not page.ok:
                continue
            results.append(_page_to_search_result(page))
        return results


class SearXNGSearchProvider:
    """Optional self-hosted metasearch plus bounded public-page extraction."""

    name = "searxng"

    def __init__(
        self,
        endpoint: str | None = None,
        timeout_seconds: float = 20.0,
        fetcher: WebPageFetcher | None = None,
    ) -> None:
        self.endpoint = (endpoint or os.getenv("SEARXNG_URL") or "").rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.fetcher = fetcher or WebPageFetcher(timeout_seconds=timeout_seconds)

    @property
    def configured(self) -> bool:
        return bool(self.endpoint)

    async def search(self, query: str, max_results: int = 3) -> list[WebSearchResult]:
        if not self.configured:
            return []
        params = urllib.parse.urlencode({"q": query, "format": "json"})
        raw = await asyncio.to_thread(
            _request_json,
            f"{self.endpoint}/search?{params}",
            None,
            self.timeout_seconds,
        )
        if not raw:
            return []
        results = raw.get("results", [])
        if not isinstance(results, list):
            return []
        candidates = [item for item in results[:max_results] if isinstance(item, dict)]
        pages = await asyncio.gather(
            *(self.fetcher.fetch(str(item.get("url") or "")) for item in candidates),
            return_exceptions=True,
        )
        parsed: list[WebSearchResult] = []
        for item, page in zip(candidates, pages, strict=False):
            if not isinstance(item, dict):
                continue
            url = str(item.get("url") or "")
            snippet = str(item.get("content") or item.get("snippet") or "")
            fetched = page if not isinstance(page, BaseException) else None
            content = fetched.text if fetched and fetched.ok else snippet
            if not url or not content:
                continue
            metadata = _lineage_metadata(
                content,
                content_origin="fetched_page" if fetched and fetched.ok else "searxng_snippet",
                fetch_status=fetched.status if fetched else "fetch_exception",
            )
            if fetched:
                metadata.update(
                    {
                        "final_url": fetched.final_url,
                        "content_type": fetched.content_type,
                        "content_sha256": fetched.content_sha256
                        or metadata["content_sha256"],
                        "retrieved_at": fetched.fetched_at,
                        "bytes_read": fetched.bytes_read,
                        "risk_flags": fetched.risk_flags,
                        "fetch_error": fetched.error,
                    }
                )
            parsed.append(
                WebSearchResult(
                    title=str(item.get("title") or url),
                    url=url,
                    content=content,
                    score=float(item.get("score") or 0.0),
                    provider=self.name,
                    metadata=metadata,
                )
            )
        return parsed


class CompositeWebSearchProvider:
    def __init__(self, providers: list[WebSearchProvider]) -> None:
        self.providers = providers

    async def search(self, query: str, max_results: int = 3) -> list[WebSearchResult]:
        batches = await asyncio.gather(
            *(provider.search(query, max_results=max_results) for provider in self.providers),
            return_exceptions=True,
        )
        merged: list[WebSearchResult] = []
        seen_urls: set[str] = set()
        valid_batches = [batch for batch in batches if not isinstance(batch, BaseException)]
        max_batch_size = max((len(batch) for batch in valid_batches), default=0)
        for index in range(max_batch_size):
            for batch in valid_batches:
                if index >= len(batch):
                    continue
                result = batch[index]
                normalized_url = result.url.rstrip("/")
                if normalized_url in seen_urls:
                    continue
                seen_urls.add(normalized_url)
                merged.append(result)
                if len(merged) >= max_results:
                    return merged
        return merged[:max_results]


class SQLiteSearchCache:
    """Small persistent TTL cache so live-search runs remain inspectable and repeatable."""

    backend_name = "sqlite"

    def __init__(self, path: str | Path, ttl_seconds: int = 3600) -> None:
        self.path = Path(path)
        self.ttl_seconds = max(0, ttl_seconds)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=10000")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS web_search_cache (
                    cache_key TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    query TEXT NOT NULL,
                    max_results INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )

    def get(self, provider: str, query: str, max_results: int) -> list[WebSearchResult] | None:
        cache_key = self._key(provider, query, max_results)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload, created_at FROM web_search_cache WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
        if row is None or time.time() - float(row[1]) > self.ttl_seconds:
            return None
        payload = json.loads(str(row[0]))
        results = [WebSearchResult(**item) for item in payload]
        for result in results:
            result.metadata.update({"cache_hit": True, "cache_backend": self.backend_name})
        return results

    def put(
        self,
        provider: str,
        query: str,
        max_results: int,
        results: list[WebSearchResult],
    ) -> None:
        cache_key = self._key(provider, query, max_results)
        payload = json.dumps([asdict(item) for item in results], ensure_ascii=False)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO web_search_cache
                (cache_key, provider, query, max_results, payload, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (cache_key, provider, query, max_results, payload, time.time()),
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10.0)
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    @staticmethod
    def _key(provider: str, query: str, max_results: int) -> str:
        raw = f"{provider}\n{query.strip()}\n{max_results}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class RedisSearchCache:
    """Optional shared TTL cache for multi-process deployments."""

    backend_name = "redis"

    def __init__(
        self,
        url: str | None = None,
        ttl_seconds: int = 3600,
        client: object | None = None,
    ) -> None:
        self.ttl_seconds = max(1, ttl_seconds)
        if client is not None:
            self.client = client
            return
        try:
            from redis import Redis
        except ImportError as exc:
            raise RuntimeError("Install the 'enterprise' extra to use Redis cache.") from exc
        self.client = Redis.from_url(
            url or os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"),
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )

    def get(self, provider: str, query: str, max_results: int) -> list[WebSearchResult] | None:
        raw = self.client.get(self._key(provider, query, max_results))
        if not raw:
            return None
        payload = json.loads(str(raw))
        results = [WebSearchResult(**item) for item in payload]
        for result in results:
            result.metadata.update({"cache_hit": True, "cache_backend": self.backend_name})
        return results

    def put(
        self,
        provider: str,
        query: str,
        max_results: int,
        results: list[WebSearchResult],
    ) -> None:
        payload = json.dumps([asdict(item) for item in results], ensure_ascii=False)
        self.client.setex(
            self._key(provider, query, max_results),
            self.ttl_seconds,
            payload,
        )

    @staticmethod
    def _key(provider: str, query: str, max_results: int) -> str:
        digest = SQLiteSearchCache._key(provider, query, max_results)
        return f"deepresearch:web-search:{digest}"


class FallbackSearchCache:
    """Use a shared primary cache and degrade to local SQLite on connection failures."""

    backend_name = "redis_with_sqlite_fallback"

    def __init__(self, primary: SearchCache, fallback: SearchCache) -> None:
        self.primary = primary
        self.fallback = fallback

    def get(self, provider: str, query: str, max_results: int) -> list[WebSearchResult] | None:
        try:
            return self.primary.get(provider, query, max_results)
        except Exception as exc:
            results = self.fallback.get(provider, query, max_results)
            if results:
                for result in results:
                    result.metadata.update(
                        {
                            "cache_backend": self.fallback.backend_name,
                            "cache_fallback_from": self.primary.backend_name,
                            "cache_error": type(exc).__name__,
                        }
                    )
            return results

    def put(
        self,
        provider: str,
        query: str,
        max_results: int,
        results: list[WebSearchResult],
    ) -> None:
        try:
            self.primary.put(provider, query, max_results, results)
        except Exception as exc:
            for result in results:
                result.metadata.update(
                    {
                        "cache_backend": self.fallback.backend_name,
                        "cache_fallback_from": self.primary.backend_name,
                        "cache_error": type(exc).__name__,
                    }
                )
            self.fallback.put(provider, query, max_results, results)


class CachedWebSearchProvider:
    def __init__(
        self,
        provider: WebSearchProvider,
        cache: SearchCache,
        provider_name: str,
    ) -> None:
        self.provider = provider
        self.cache = cache
        self.provider_name = provider_name

    async def search(self, query: str, max_results: int = 3) -> list[WebSearchResult]:
        cache_error: str | None = None
        try:
            cached = await asyncio.to_thread(
                self.cache.get, self.provider_name, query, max_results
            )
        except Exception as exc:
            cached = None
            cache_error = type(exc).__name__
        if cached is not None:
            return cached
        results = await self.provider.search(query, max_results=max_results)
        for result in results:
            result.metadata["cache_hit"] = False
            result.metadata["cache_backend"] = self.cache.backend_name
            if cache_error:
                result.metadata["cache_error"] = cache_error
        if results:
            try:
                await asyncio.to_thread(
                    self.cache.put,
                    self.provider_name,
                    query,
                    max_results,
                    results,
                )
            except Exception as exc:
                for result in results:
                    result.metadata["cache_error"] = type(exc).__name__
        return results


def create_web_search_provider(
    provider: str = "disabled",
    cache_path: str | Path | None = None,
    cache_ttl_seconds: int = 3600,
    cache_backend: str = "sqlite",
    redis_url: str | None = None,
) -> WebSearchProvider:
    names = [name.strip().lower() for name in provider.split(",") if name.strip()]
    providers: list[WebSearchProvider] = []
    for name in names:
        if name == "tavily":
            base: WebSearchProvider = TavilySearchProvider()
        elif name == "wikipedia":
            base = WikipediaSearchProvider()
        elif name == "arxiv":
            base = ArxivSearchProvider()
        elif name == "github":
            base = GitHubSearchProvider()
        elif name == "url":
            base = DirectURLProvider()
        elif name == "searxng":
            base = SearXNGSearchProvider()
        else:
            continue
        providers.append(
            ResilientWebSearchProvider(
                base,
                name,
                timeout_seconds=25.0,
                max_retries=1,
                failure_threshold=3,
                reset_seconds=30.0,
                max_concurrency=1 if name == "github" else 3 if name == "url" else 2,
                min_interval_seconds=0.25 if name == "github" else 0.0,
            )
        )
    if not providers:
        return DisabledWebSearchProvider()
    selected: WebSearchProvider = (
        providers[0] if len(providers) == 1 else CompositeWebSearchProvider(providers)
    )
    if cache_path:
        cache: SearchCache
        if cache_backend == "redis":
            try:
                cache = FallbackSearchCache(
                    RedisSearchCache(redis_url, ttl_seconds=cache_ttl_seconds),
                    SQLiteSearchCache(cache_path, ttl_seconds=cache_ttl_seconds),
                )
            except RuntimeError:
                cache = SQLiteSearchCache(cache_path, ttl_seconds=cache_ttl_seconds)
        else:
            cache = SQLiteSearchCache(cache_path, ttl_seconds=cache_ttl_seconds)
        selected = CachedWebSearchProvider(
            selected,
            cache,
            provider_name=",".join(names),
        )
    return selected


def provider_telemetry(provider: WebSearchProvider) -> dict[str, object]:
    """Collect bounded telemetry from nested cached/composite provider graphs."""
    events: list[dict[str, object]] = []

    def visit(current: object) -> None:
        if isinstance(current, ResilientWebSearchProvider):
            events.extend(current.telemetry_snapshot())
            return
        if isinstance(current, CachedWebSearchProvider):
            visit(current.provider)
            return
        if isinstance(current, CompositeWebSearchProvider):
            for child in current.providers:
                visit(child)

    visit(provider)
    status_counts: dict[str, int] = {}
    provider_counts: dict[str, int] = {}
    for event in events:
        status = str(event.get("status") or "unknown")
        provider_name = str(event.get("provider") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        provider_counts[provider_name] = provider_counts.get(provider_name, 0) + 1
    event_count = len(events)
    operational_count = sum(
        count for status, count in status_counts.items() if status in {"success", "empty"}
    )
    latencies = [float(event.get("latency_seconds") or 0.0) for event in events]
    summary = {
        "event_count": event_count,
        "status_counts": status_counts,
        "provider_counts": provider_counts,
        "operational_rate": operational_count / event_count if event_count else 0.0,
        "total_retries": sum(int(event.get("retries") or 0) for event in events),
        "mean_latency_seconds": sum(latencies) / event_count if event_count else 0.0,
        "max_latency_seconds": max(latencies, default=0.0),
        "circuit_open_count": status_counts.get("circuit_open", 0),
    }
    return {"summary": summary, "events": events}


def web_search_status(provider: str = "disabled") -> dict:
    names = [name.strip().lower() for name in provider.split(",") if name.strip()]
    details = []
    for name in names:
        if name == "tavily":
            details.append(
                {
                    "provider": name,
                    "env_var": "TAVILY_API_KEY",
                    "configured": bool(os.getenv("TAVILY_API_KEY")),
                }
            )
        elif name == "searxng":
            details.append(
                {
                    "provider": name,
                    "env_var": "SEARXNG_URL",
                    "configured": bool(os.getenv("SEARXNG_URL")),
                }
            )
        elif name == "wikipedia":
            details.append({"provider": name, "env_var": None, "configured": True})
        elif name == "arxiv":
            details.append({"provider": name, "env_var": None, "configured": True})
        elif name == "github":
            details.append(
                {
                    "provider": name,
                    "env_var": "GITHUB_TOKEN",
                    "configured": True,
                    "authenticated": bool(os.getenv("GITHUB_TOKEN")),
                }
            )
        elif name == "url":
            details.append({"provider": name, "env_var": None, "configured": True})
    return {
        "provider": provider if details else "disabled",
        "providers": details,
        "env_configured": any(item["configured"] for item in details),
        "enabled_by_default": False,
    }


def _request_json(
    url: str,
    payload: dict | None,
    timeout_seconds: float,
    extra_headers: dict[str, str] | None = None,
) -> dict | None:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    headers.update(extra_headers or {})
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="POST" if data is not None else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ProviderRequestError(f"JSON request failed: {type(exc).__name__}") from exc


def _request_bytes(url: str, timeout_seconds: float) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/atom+xml", "User-Agent": USER_AGENT},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return response.read(5_000_000)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ProviderRequestError(f"Byte request failed: {type(exc).__name__}") from exc


def _request_text(
    url: str,
    timeout_seconds: float,
    headers: dict[str, str] | None = None,
) -> str:
    request_headers = {"User-Agent": USER_AGENT}
    request_headers.update(headers or {})
    request = urllib.request.Request(url, headers=request_headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return response.read(1_000_000).decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ProviderRequestError(f"Text request failed: {type(exc).__name__}") from exc


def _lineage_metadata(
    content: str,
    *,
    content_origin: str,
    fetch_status: str,
) -> dict[str, object]:
    return {
        "content_origin": content_origin,
        "fetch_status": fetch_status,
        "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "cache_hit": False,
        "risk_flags": [],
    }


def _collapse_whitespace(text: str) -> str:
    return " ".join(text.split())


def _page_to_search_result(page: FetchedPage) -> WebSearchResult:
    parsed = urllib.parse.urlparse(page.final_url)
    title = parsed.path.rstrip("/").rsplit("/", maxsplit=1)[-1] or parsed.hostname or page.final_url
    return WebSearchResult(
        title=urllib.parse.unquote(title),
        url=page.final_url,
        content=page.text,
        score=1.0,
        provider="url",
        source_type="web_page",
        trust_level="medium",
        metadata={
            **_lineage_metadata(
                page.text,
                content_origin="direct_url_fetch",
                fetch_status=page.status,
            ),
            "final_url": page.final_url,
            "content_type": page.content_type,
            "bytes_read": page.bytes_read,
            "risk_flags": page.risk_flags,
            "fetch_error": page.error,
        },
    )
