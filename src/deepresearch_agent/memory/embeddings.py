from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sqlite3
import time
import urllib.request
from pathlib import Path
from typing import Protocol
from urllib.error import HTTPError
from urllib.parse import urlparse

import numpy as np


class EmbeddingProviderHTTPError(RuntimeError):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(f"embedding provider returned HTTP {status_code}: {detail}")
        self.status_code = status_code


class EmbeddingProvider(Protocol):
    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Return one normalized vector for every input, preserving order."""

    def status(self) -> dict[str, object]:
        """Return secret-free configuration and bounded runtime telemetry."""


class SQLiteEmbeddingCache:
    """Persistent content-addressed cache for model-specific embedding vectors."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5.0)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS embedding_cache (
                    cache_key TEXT PRIMARY KEY,
                    vector_json TEXT NOT NULL,
                    dimensions INTEGER NOT NULL CHECK (dimensions > 0),
                    created_at REAL NOT NULL
                )
                """
            )

    def get_many(self, keys: list[str]) -> dict[str, list[float]]:
        if not keys:
            return {}
        placeholders = ",".join("?" for _ in keys)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT cache_key, vector_json FROM embedding_cache "  # noqa: S608
                f"WHERE cache_key IN ({placeholders})",
                keys,
            ).fetchall()
        return {str(key): [float(value) for value in json.loads(vector)] for key, vector in rows}

    def set_many(self, values: dict[str, list[float]]) -> None:
        if not values:
            return
        now = time.time()
        rows = [
            (key, json.dumps(vector, separators=(",", ":")), len(vector), now)
            for key, vector in values.items()
        ]
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO embedding_cache(cache_key, vector_json, dimensions, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    vector_json = excluded.vector_json,
                    dimensions = excluded.dimensions,
                    created_at = excluded.created_at
                """,
                rows,
            )


class OpenAICompatibleEmbeddingProvider:
    """Batch embedding client with retry, normalization, and SQLite cache."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key_env: str = "EMBEDDING_API_KEY",
        cache_path: str | Path = "data/memory/embedding_cache.sqlite3",
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
        batch_size: int = 64,
    ) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("embedding base_url must be an absolute http(s) URL")
        if parsed.username or parsed.password:
            raise ValueError("embedding base_url must not contain credentials")
        if not model.strip():
            raise ValueError("embedding model must not be empty")
        if not api_key_env.strip():
            raise ValueError("embedding api_key_env must not be empty")
        if batch_size < 1:
            raise ValueError("embedding batch_size must be at least 1")
        if timeout_seconds <= 0:
            raise ValueError("embedding timeout_seconds must be positive")
        if max_retries < 0:
            raise ValueError("embedding max_retries must not be negative")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key_env = api_key_env
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.requested_batch_size = batch_size
        self.batch_size = self._effective_batch_size(parsed.netloc, model, batch_size)
        self.cache = SQLiteEmbeddingCache(cache_path)
        self._telemetry: dict[str, int | float | str | None] = {
            "requests": 0,
            "remote_inputs": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "retries": 0,
            "errors": 0,
            "prompt_tokens": 0,
            "total_tokens": 0,
            "last_latency_seconds": None,
        }
        namespace = f"{self.base_url}\0{self.model}"
        self._namespace = hashlib.sha256(namespace.encode("utf-8")).hexdigest()[:16]

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        keys = [self._cache_key(text) for text in texts]
        cached = self.cache.get_many(list(dict.fromkeys(keys)))
        self._telemetry["cache_hits"] = int(self._telemetry["cache_hits"]) + sum(
            1 for key in keys if key in cached
        )

        missing_by_key: dict[str, str] = {}
        for key, text in zip(keys, texts, strict=True):
            if key not in cached:
                missing_by_key.setdefault(key, text)
        self._telemetry["cache_misses"] = int(self._telemetry["cache_misses"]) + len(
            missing_by_key
        )

        missing_items = list(missing_by_key.items())
        for start in range(0, len(missing_items), self.batch_size):
            batch = missing_items[start : start + self.batch_size]
            vectors = await self._request_batch([text for _, text in batch])
            normalized = [self._normalize(vector) for vector in vectors]
            new_values = {
                key: vector for (key, _), vector in zip(batch, normalized, strict=True)
            }
            self.cache.set_many(new_values)
            cached.update(new_values)

        vectors = [cached[key] for key in keys]
        dimensions = {len(vector) for vector in vectors}
        if len(dimensions) != 1 or 0 in dimensions:
            raise RuntimeError("embedding provider returned inconsistent vector dimensions")
        return vectors

    async def _request_batch(self, texts: list[str]) -> list[list[float]]:
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"Missing API key environment variable: {self.api_key_env}")
        body = json.dumps({"model": self.model, "input": texts}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/embeddings",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            started = time.perf_counter()
            try:
                payload = await asyncio.to_thread(self._send, request)
                self._telemetry["requests"] = int(self._telemetry["requests"]) + 1
                self._telemetry["remote_inputs"] = int(
                    self._telemetry["remote_inputs"]
                ) + len(texts)
                self._telemetry["last_latency_seconds"] = round(
                    time.perf_counter() - started, 6
                )
                self._record_usage(payload)
                return self._parse_vectors(payload, len(texts))
            except Exception as exc:  # noqa: BLE001 - bounded transport retry.
                last_error = exc
                retryable = not isinstance(exc, EmbeddingProviderHTTPError) or exc.status_code in {
                    408,
                    409,
                    429,
                    500,
                    502,
                    503,
                    504,
                }
                if attempt < self.max_retries and retryable:
                    self._telemetry["retries"] = int(self._telemetry["retries"]) + 1
                    await asyncio.sleep(0.25 * (2**attempt))
                elif not retryable:
                    break
        self._telemetry["errors"] = int(self._telemetry["errors"]) + 1
        raise RuntimeError(f"embedding request failed: {last_error}") from last_error

    def _record_usage(self, payload: dict[str, object]) -> None:
        usage = payload.get("usage")
        if not isinstance(usage, dict):
            return
        prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
        total_tokens = int(usage.get("total_tokens", prompt_tokens) or prompt_tokens)
        self._telemetry["prompt_tokens"] = (
            int(self._telemetry["prompt_tokens"]) + prompt_tokens
        )
        self._telemetry["total_tokens"] = int(self._telemetry["total_tokens"]) + total_tokens

    def _send(self, request: urllib.request.Request) -> dict[str, object]:
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise EmbeddingProviderHTTPError(
                exc.code,
                self._safe_error_detail(exc.read()),
            ) from exc

    @staticmethod
    def _safe_error_detail(body: bytes) -> str:
        try:
            payload = json.loads(body.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            return "provider rejected the request"
        if not isinstance(payload, dict):
            return "provider rejected the request"
        error = payload.get("error", payload)
        if not isinstance(error, dict):
            return "provider rejected the request"
        code = str(error.get("code", "")).strip()
        message = str(error.get("message", "")).strip()
        detail = ": ".join(value for value in (code, message) if value)
        return detail[:500] or "provider rejected the request"

    def _parse_vectors(
        self, payload: dict[str, object], expected_count: int
    ) -> list[list[float]]:
        data = payload.get("data")
        if not isinstance(data, list) or len(data) != expected_count:
            raise RuntimeError("embedding response count does not match request")
        indexes = [int(item.get("index", -1)) for item in data if isinstance(item, dict)]
        if sorted(indexes) != list(range(expected_count)):
            raise RuntimeError("embedding response indexes do not match request")
        ordered = sorted(data, key=lambda item: int(item.get("index", 0)))
        vectors: list[list[float]] = []
        for item in ordered:
            if not isinstance(item, dict) or not isinstance(item.get("embedding"), list):
                raise RuntimeError("embedding response contains an invalid item")
            vectors.append([float(value) for value in item["embedding"]])
        return vectors

    def _normalize(self, vector: list[float]) -> list[float]:
        values = np.asarray(vector, dtype=np.float32)
        if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
            raise RuntimeError("embedding response contains an invalid vector")
        norm = float(np.linalg.norm(values))
        if norm == 0:
            raise RuntimeError("embedding response contains a zero vector")
        return (values / norm).tolist()

    def _cache_key(self, text: str) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"{self._namespace}:{digest}"

    @staticmethod
    def _effective_batch_size(host: str, model: str, requested: int) -> int:
        # Alibaba Cloud documents a maximum of 10 text inputs per synchronous
        # text-embedding-v4 request. Clamp only this known provider/model pair;
        # other OpenAI-compatible services retain the caller's requested size.
        if host.lower() == "dashscope.aliyuncs.com" and model == "text-embedding-v4":
            return min(requested, 10)
        return requested

    def status(self) -> dict[str, object]:
        return {
            "provider": "openai_compatible",
            "base_url": self.base_url,
            "model": self.model,
            "api_key_env": self.api_key_env,
            "env_configured": bool(os.getenv(self.api_key_env)),
            "cache_backend": "sqlite",
            "cache_path": self.cache.path.as_posix(),
            "batch_size": self.batch_size,
            "requested_batch_size": self.requested_batch_size,
            **self._telemetry,
        }
