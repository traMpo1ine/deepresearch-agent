from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class LLMMessage:
    role: str
    content: str


class LLMBackend(Protocol):
    async def complete(self, messages: list[LLMMessage]) -> str:
        """Return a model completion for a chat-style message list."""

    async def structured_complete(self, messages: list[LLMMessage]) -> dict[str, Any]:
        """Return a JSON-like object for structured agent outputs."""

    async def embed(self, text: str) -> list[float]:
        """Return an embedding vector when the backend supports embeddings."""
