from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from .base import LLMBackend
from .mock import MockLLMBackend
from .openai_compatible import DeepSeekBackend, OpenAIBackend, VLLMBackend


BackendName = Literal["mock", "openai", "deepseek", "vllm"]


@dataclass(slots=True)
class LLMBackendConfig:
    backend: BackendName = "mock"
    model: str | None = None
    timeout_seconds: float = 60.0
    max_retries: int = 2
    vllm_base_url: str = "http://localhost:8000/v1"
    max_tokens: int | None = None


def create_llm_backend(config: LLMBackendConfig) -> LLMBackend:
    if config.backend == "mock":
        return MockLLMBackend()
    if config.backend == "openai":
        return OpenAIBackend(
            model=config.model or "gpt-4o-mini",
            timeout_seconds=config.timeout_seconds,
            max_retries=config.max_retries,
            max_tokens=config.max_tokens,
        )
    if config.backend == "deepseek":
        return DeepSeekBackend(
            model=config.model or "deepseek-v4-flash",
            timeout_seconds=config.timeout_seconds,
            max_retries=config.max_retries,
            max_tokens=512 if config.max_tokens is None else config.max_tokens,
        )
    if config.backend == "vllm":
        return VLLMBackend(
            base_url=config.vllm_base_url,
            model=config.model or "local-model",
            timeout_seconds=config.timeout_seconds,
            max_retries=config.max_retries,
            max_tokens=config.max_tokens,
        )
    raise ValueError(f"Unknown LLM backend: {config.backend}")


def backend_status(config: LLMBackendConfig) -> dict:
    env_var = {
        "mock": None,
        "openai": "OPENAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "vllm": "VLLM_API_KEY",
    }[config.backend]
    return {
        "backend": config.backend,
        "model": _resolved_model(config),
        "timeout_seconds": config.timeout_seconds,
        "max_retries": config.max_retries,
        "max_tokens": 512 if config.backend == "deepseek" and config.max_tokens is None else config.max_tokens,
        "env_var": env_var,
        "env_configured": True if env_var is None else bool(os.getenv(env_var)),
        "offline_safe": config.backend == "mock",
        "base_url": _base_url(config),
    }


def _resolved_model(config: LLMBackendConfig) -> str:
    defaults = {
        "mock": "mock-researcher-v0",
        "openai": "gpt-4o-mini",
        "deepseek": "deepseek-v4-flash",
        "vllm": "local-model",
    }
    return config.model or defaults[config.backend]


def _base_url(config: LLMBackendConfig) -> str:
    return {
        "mock": "local://mock",
        "openai": "https://api.openai.com/v1",
        "deepseek": "https://api.deepseek.com",
        "vllm": config.vllm_base_url,
    }[config.backend]
