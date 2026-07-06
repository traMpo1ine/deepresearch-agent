from __future__ import annotations

from deepresearch_agent.memory.vector_index import NumpyVectorIndex

from .base import LLMMessage


class MockLLMBackend:
    def __init__(self) -> None:
        self.index = NumpyVectorIndex(dim=64)

    async def complete(self, messages: list[LLMMessage]) -> str:
        prompt = messages[-1].content if messages else ""
        return f"Mock response for: {prompt[:120]}"

    async def structured_complete(self, messages: list[LLMMessage]) -> dict:
        content = await self.complete(messages)
        return {"content": content, "backend": "mock"}

    async def embed(self, text: str) -> list[float]:
        return self.index.embed_text(text).tolist()
