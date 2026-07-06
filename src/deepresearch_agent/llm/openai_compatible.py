from __future__ import annotations

import asyncio
import json
import os
import time
import urllib.request
from typing import Any

from deepresearch_agent.structured_output import StructuredOutputParser

from .base import LLMMessage


class OpenAICompatibleBackend:
    def __init__(
        self,
        base_url: str,
        api_key_env: str,
        model: str,
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
        max_tokens: int | None = None,
        extra_payload: dict[str, Any] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key_env = api_key_env
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_tokens = max_tokens
        self.extra_payload = extra_payload or {}
        self.last_usage: dict[str, Any] = {}
        self.total_cost_estimate = 0.0

    async def complete(self, messages: list[LLMMessage]) -> str:
        started = time.perf_counter()
        payload = {
            "model": self.model,
            "messages": [{"role": message.role, "content": message.content} for message in messages],
            "temperature": 0.2,
        }
        if self.max_tokens is not None:
            payload["max_tokens"] = self.max_tokens
        payload.update(self.extra_payload)
        response = await self._post_json("/chat/completions", payload)
        self._record_usage(response, time.perf_counter() - started)
        return response["choices"][0]["message"]["content"]

    async def structured_complete(self, messages: list[LLMMessage]) -> dict[str, Any]:
        text = await self.complete(messages)
        result = StructuredOutputParser().parse(text, schema_defaults={"content": text})
        return {**result.data, "__parse_metadata__": result.metadata()}

    async def embed(self, text: str) -> list[float]:
        payload = {"model": "text-embedding-3-small", "input": text}
        started = time.perf_counter()
        response = await self._post_json("/embeddings", payload)
        self._record_usage(response, time.perf_counter() - started)
        return list(response["data"][0]["embedding"])

    def _record_usage(self, response: dict[str, Any], latency_seconds: float) -> None:
        usage = response.get("usage", {})
        prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
        completion_tokens = int(usage.get("completion_tokens", 0) or 0)
        total_tokens = int(usage.get("total_tokens", prompt_tokens + completion_tokens) or 0)
        prompt_cache_hit_tokens = int(usage.get("prompt_cache_hit_tokens", 0) or 0)
        prompt_cache_miss_tokens = int(
            usage.get("prompt_cache_miss_tokens", max(prompt_tokens - prompt_cache_hit_tokens, 0)) or 0
        )
        cost_estimate, pricing_source = self._estimate_cost(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            prompt_cache_hit_tokens=prompt_cache_hit_tokens,
            prompt_cache_miss_tokens=prompt_cache_miss_tokens,
        )
        self.last_usage = {
            "model": self.model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "prompt_cache_hit_tokens": prompt_cache_hit_tokens,
            "prompt_cache_miss_tokens": prompt_cache_miss_tokens,
            "latency_seconds": latency_seconds,
            "cost_estimate": cost_estimate,
            "cost_estimate_usd": cost_estimate,
            "pricing_source": pricing_source,
        }
        self.total_cost_estimate += cost_estimate

    def _estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        prompt_cache_hit_tokens: int,
        prompt_cache_miss_tokens: int,
    ) -> tuple[float, str]:
        if self.base_url != "https://api.deepseek.com":
            return 0.0, "not_configured"
        pricing = _deepseek_pricing_for_model(self.model)
        if pricing is None:
            return 0.0, "unknown_deepseek_model"
        if prompt_cache_hit_tokens == 0 and prompt_cache_miss_tokens == 0:
            prompt_cache_miss_tokens = prompt_tokens
        cost = (
            prompt_cache_hit_tokens * pricing["input_cache_hit"]
            + prompt_cache_miss_tokens * pricing["input_cache_miss"]
            + completion_tokens * pricing["output"]
        ) / 1_000_000
        return cost, "deepseek_api_docs_2026_07"

    async def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"Missing API key environment variable: {self.api_key_env}")
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        last_error: Exception | None = None
        for _ in range(self.max_retries + 1):
            try:
                return await asyncio.to_thread(self._send, request)
            except Exception as exc:  # noqa: BLE001 - retry wrapper.
                last_error = exc
                await asyncio.sleep(0.5)
        raise RuntimeError(f"LLM request failed: {last_error}")

    def _send(self, request: urllib.request.Request) -> dict[str, Any]:
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))


class DeepSeekBackend(OpenAICompatibleBackend):
    def __init__(
        self,
        model: str = "deepseek-v4-flash",
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
        max_tokens: int | None = 512,
    ) -> None:
        super().__init__(
            base_url="https://api.deepseek.com",
            api_key_env="DEEPSEEK_API_KEY",
            model=model,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            max_tokens=max_tokens,
            extra_payload={"thinking": {"type": "disabled"}},
        )


class OpenAIBackend(OpenAICompatibleBackend):
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
        max_tokens: int | None = None,
    ) -> None:
        super().__init__(
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            model=model,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            max_tokens=max_tokens,
        )


class VLLMBackend(OpenAICompatibleBackend):
    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        model: str = "local-model",
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
        max_tokens: int | None = None,
    ) -> None:
        super().__init__(
            base_url=base_url,
            api_key_env="VLLM_API_KEY",
            model=model,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            max_tokens=max_tokens,
        )


DEEPSEEK_PRICING_PER_1M_TOKENS_USD = {
    "deepseek-v4-flash": {
        "input_cache_hit": 0.0028,
        "input_cache_miss": 0.14,
        "output": 0.28,
    },
    "deepseek-v4-pro": {
        "input_cache_hit": 0.003625,
        "input_cache_miss": 0.435,
        "output": 0.87,
    },
}

DEEPSEEK_MODEL_ALIASES = {
    "deepseek-chat": "deepseek-v4-flash",
    "deepseek-reasoner": "deepseek-v4-flash",
}


def _deepseek_pricing_for_model(model: str) -> dict[str, float] | None:
    canonical = DEEPSEEK_MODEL_ALIASES.get(model, model)
    return DEEPSEEK_PRICING_PER_1M_TOKENS_USD.get(canonical)
