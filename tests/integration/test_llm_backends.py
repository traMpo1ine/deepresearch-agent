import os

import pytest

from deepresearch_agent.llm import DeepSeekBackend, LLMMessage, OpenAIBackend, VLLMBackend


@pytest.mark.asyncio
async def test_openai_backend_smoke_when_key_is_available() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is not set.")
    backend = OpenAIBackend(model=os.getenv("OPENAI_TEST_MODEL", "gpt-4o-mini"), timeout_seconds=30)
    text = await backend.complete([LLMMessage(role="user", content="Reply with ok.")])
    assert text


@pytest.mark.asyncio
async def test_deepseek_backend_smoke_when_key_is_available() -> None:
    if not os.getenv("DEEPSEEK_API_KEY"):
        pytest.skip("DEEPSEEK_API_KEY is not set.")
    backend = DeepSeekBackend(model=os.getenv("DEEPSEEK_TEST_MODEL", "deepseek-v4-flash"), timeout_seconds=30)
    text = await backend.complete([LLMMessage(role="user", content="Reply with ok.")])
    assert text


@pytest.mark.asyncio
async def test_vllm_backend_smoke_when_key_is_available() -> None:
    if not os.getenv("VLLM_API_KEY"):
        pytest.skip("VLLM_API_KEY is not set.")
    backend = VLLMBackend(model=os.getenv("VLLM_TEST_MODEL", "local-model"), timeout_seconds=30)
    text = await backend.complete([LLMMessage(role="user", content="Reply with ok.")])
    assert text
