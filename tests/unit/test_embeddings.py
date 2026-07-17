from __future__ import annotations

import json

import pytest

from deepresearch_agent.memory.embeddings import (
    EmbeddingProviderHTTPError,
    OpenAICompatibleEmbeddingProvider,
)


class _FakeEmbeddingProvider(OpenAICompatibleEmbeddingProvider):
    def __init__(self, cache_path) -> None:
        super().__init__(
            base_url="https://embedding.example/v1",
            model="example-embedding-v1",
            cache_path=cache_path,
            max_retries=0,
        )
        self.remote_batches: list[list[str]] = []

    async def _request_batch(self, texts: list[str]) -> list[list[float]]:
        self.remote_batches.append(texts)
        return [[float(index + 1), 1.0] for index, _ in enumerate(texts)]


@pytest.mark.asyncio
async def test_embedding_provider_batches_deduplicates_and_caches(tmp_path) -> None:
    provider = _FakeEmbeddingProvider(tmp_path / "embeddings.sqlite3")

    first = await provider.embed_many(["alpha", "beta", "alpha"])
    second = await provider.embed_many(["alpha", "beta"])

    assert len(first) == 3
    assert first[0] == first[2]
    assert first[0] == second[0]
    assert provider.remote_batches == [["alpha", "beta"]]
    assert provider.status()["cache_hits"] == 2
    assert provider.status()["cache_misses"] == 2


def test_embedding_provider_parses_response_by_index(tmp_path) -> None:
    provider = _FakeEmbeddingProvider(tmp_path / "embeddings.sqlite3")
    payload = {
        "data": [
            {"index": 1, "embedding": [0.0, 2.0]},
            {"index": 0, "embedding": [1.0, 0.0]},
        ]
    }

    assert provider._parse_vectors(payload, 2) == [[1.0, 0.0], [0.0, 2.0]]
    with pytest.raises(RuntimeError, match="count"):
        provider._parse_vectors(json.loads('{"data": []}'), 1)


def test_embedding_provider_status_does_not_expose_secret(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("EMBEDDING_API_KEY", "super-secret")
    provider = _FakeEmbeddingProvider(tmp_path / "embeddings.sqlite3")

    status = provider.status()

    assert status["env_configured"] is True
    assert "super-secret" not in json.dumps(status)


def test_embedding_provider_rejects_credentials_in_base_url(tmp_path) -> None:
    with pytest.raises(ValueError, match="credentials"):
        OpenAICompatibleEmbeddingProvider(
            base_url="https://user:password@example.com/v1",
            model="example",
            cache_path=tmp_path / "embeddings.sqlite3",
        )


def test_embedding_provider_accumulates_secret_free_usage(tmp_path) -> None:
    provider = _FakeEmbeddingProvider(tmp_path / "embeddings.sqlite3")

    provider._record_usage({"usage": {"prompt_tokens": 12, "total_tokens": 12}})
    provider._record_usage({"usage": {"prompt_tokens": 8, "total_tokens": 8}})

    assert provider.status()["prompt_tokens"] == 20
    assert provider.status()["total_tokens"] == 20


def test_dashscope_text_embedding_v4_clamps_batch_size_to_documented_limit(tmp_path) -> None:
    provider = OpenAICompatibleEmbeddingProvider(
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="text-embedding-v4",
        cache_path=tmp_path / "embeddings.sqlite3",
        batch_size=64,
    )

    status = provider.status()

    assert status["requested_batch_size"] == 64
    assert status["batch_size"] == 10


@pytest.mark.asyncio
async def test_embedding_provider_does_not_retry_http_400(monkeypatch, tmp_path) -> None:
    provider = OpenAICompatibleEmbeddingProvider(
        base_url="https://embedding.example/v1",
        model="example",
        cache_path=tmp_path / "embeddings.sqlite3",
        max_retries=2,
    )
    attempts = 0

    def fake_send(request):
        nonlocal attempts
        attempts += 1
        raise EmbeddingProviderHTTPError(400, "account configuration error")

    monkeypatch.setenv("EMBEDDING_API_KEY", "test-only")
    monkeypatch.setattr(provider, "_send", fake_send)

    with pytest.raises(RuntimeError, match="account configuration error"):
        await provider.embed_many(["hello"])

    assert attempts == 1
    assert provider.status()["retries"] == 0
