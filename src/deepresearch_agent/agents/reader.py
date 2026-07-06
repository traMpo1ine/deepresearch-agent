from __future__ import annotations

import re

from deepresearch_agent.agents.base import BaseAgent
from deepresearch_agent.agents.searcher import SearchResult
from deepresearch_agent.schemas import Evidence, ResearchTask


class ReaderAgent(BaseAgent):
    name = "reader"

    async def _run(self, agent_input: object, context=None) -> list[Evidence]:
        if not isinstance(agent_input, dict):
            raise TypeError("ReaderAgent.run expects {'task': ResearchTask, 'results': list[SearchResult]}.")
        task = agent_input.get("task")
        results = agent_input.get("results")
        if not isinstance(task, ResearchTask) or not isinstance(results, list):
            raise TypeError("ReaderAgent.run expects {'task': ResearchTask, 'results': list[SearchResult]}.")
        return await self.read(task, results)

    async def read(self, task: ResearchTask, results: list[SearchResult]) -> list[Evidence]:
        evidence: list[Evidence] = []
        seen: set[tuple[str, str]] = set()
        for result in results:
            for index, chunk in enumerate(self._chunks(result.text), start=1):
                quote = self._best_quote(chunk, result.snippet)
                dedupe_key = (result.source_id, quote)
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                quote_start = chunk.find(quote)
                evidence.append(
                    Evidence(
                        task_id=task.id,
                        title=result.title,
                        text=chunk,
                        url=result.url,
                        quote=quote,
                        source_id=result.source_id,
                        chunk_id=f"{result.source_id}#chunk-{index}",
                        quote_start=quote_start if quote_start >= 0 else None,
                        quote_end=quote_start + len(quote) if quote_start >= 0 else None,
                        score=result.score,
                        metadata={
                            "agent": self.name,
                            "task_question": task.question,
                            "chunk_index": index,
                            "dedupe_key": f"{result.source_id}:{quote}",
                            "source_type": result.source_type,
                            "topics": result.topics or [],
                            "trust_level": result.trust_level,
                            "lexical_score": result.lexical_score,
                            "vector_score": result.vector_score,
                            "hybrid_score": result.hybrid_score,
                        },
                    )
                )
        return evidence

    def _chunks(self, text: str, max_chars: int = 420) -> list[str]:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?。！？])\s+", text) if s.strip()]
        chunks: list[str] = []
        current = ""
        for sentence in sentences:
            if len(current) + len(sentence) + 1 > max_chars and current:
                chunks.append(current.strip())
                current = sentence
            else:
                current = f"{current} {sentence}".strip()
        if current:
            chunks.append(current)
        return chunks or [text[:max_chars]]

    def _best_quote(self, chunk: str, snippet: str) -> str:
        if snippet and snippet in chunk:
            return snippet
        sentences = [s.strip() for s in re.split(r"(?<=[.!?。！？])\s+", chunk) if s.strip()]
        return sentences[0] if sentences else chunk[:180]
