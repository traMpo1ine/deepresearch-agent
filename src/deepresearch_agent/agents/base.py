from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from deepresearch_agent.schemas import AgentResult


@dataclass(slots=True)
class AgentContext:
    run_id: str
    metadata: dict[str, Any]


class BaseAgent:
    name = "base"

    async def run(
        self,
        agent_input: object,
        context: AgentContext | None = None,
    ) -> AgentResult[object]:
        """Unified agent entrypoint; specialized agents may wrap their own methods."""
        metadata = dict(context.metadata) if context else None
        return await self.timed(lambda: self._run(agent_input, context), metadata)

    async def _run(
        self,
        agent_input: object,
        context: AgentContext | None = None,
    ) -> object:
        raise NotImplementedError(f"{self.__class__.__name__} must implement _run or override run")

    async def timed(
        self,
        operation: Callable[[], Awaitable[object]],
        metadata: dict[str, Any] | None = None,
    ) -> AgentResult[object]:
        started = time.perf_counter()
        try:
            output = await operation()
            return AgentResult(
                agent_name=self.name,
                ok=True,
                output=output,
                latency_seconds=time.perf_counter() - started,
                metadata=metadata or {},
            )
        except Exception as exc:  # noqa: BLE001 - stored for agent trace visibility.
            return AgentResult(
                agent_name=self.name,
                ok=False,
                error=str(exc),
                latency_seconds=time.perf_counter() - started,
                metadata=metadata or {},
            )
