from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

from deepresearch_agent.agents.base import BaseAgent
from deepresearch_agent.memory import NumpyVectorIndex
from deepresearch_agent.schemas import ResearchTask


@dataclass(slots=True)
class SearchResult:
    source_id: str
    title: str
    snippet: str
    url: str
    score: float
    text: str
    lexical_score: float = 0.0
    vector_score: float = 0.0
    hybrid_score: float = 0.0
    source_type: str = "local_note"
    topics: list[str] | None = None
    trust_level: str = "medium"


class SearcherAgent(BaseAgent):
    name = "searcher"
    QUERY_EXPANSIONS = {
        "比较": ["compare", "comparison", "tradeoffs", "criteria", "strengths", "limitations"],
        "对比": ["compare", "comparison", "tradeoffs", "criteria", "strengths", "limitations"],
        "区别": ["difference", "compare", "tradeoffs"],
        "优缺点": ["strengths", "limitations", "tradeoffs"],
        "数据库": ["database", "storage", "memory"],
        "向量数据库": ["vector", "database", "embedding", "retrieval", "similarity", "index"],
        "向量": ["vector", "embedding", "retrieval", "similarity"],
        "语义": ["semantic", "similarity", "embedding"],
        "引用": ["citation", "evidence", "source", "quote"],
        "验证": ["verification", "verifier", "claim", "evidence"],
        "幻觉": ["hallucination", "unsupported", "contradiction"],
        "风险": ["risk", "failure", "reliability", "limitation"],
        "方案": ["design", "architecture", "implementation"],
        "架构": ["architecture", "design", "modules"],
        "实现": ["implementation", "mechanism", "engineering"],
        "sqlite": ["sqlite", "relational", "persistent", "memory", "trace"],
        "vector database": ["vector", "database", "embedding", "retrieval", "similarity", "index"],
        "vector retrieval": ["vector", "embedding", "retrieval", "similarity"],
        "compare": ["comparison", "tradeoffs", "criteria", "strengths", "limitations"],
    }

    def __init__(self, corpus_path: str | Path = "data/corpus/offline_corpus.jsonl") -> None:
        self.corpus_path = Path(corpus_path)
        self.documents = self._load_corpus(self.corpus_path)
        self.doc_freq = self._document_frequency(self.documents)
        self.vector_index = NumpyVectorIndex(dim=64)

    async def _run(self, agent_input: object, context=None) -> list[SearchResult]:
        if not isinstance(agent_input, ResearchTask):
            raise TypeError("SearcherAgent.run expects a ResearchTask.")
        return await self.search(agent_input)

    async def search(self, task: ResearchTask) -> list[SearchResult]:
        query_terms = self._query_terms(task.question)
        scored = []
        query_vector = self.vector_index.embed_text(task.question)
        for doc in self.documents:
            text_terms = self._tokens(f"{doc['title']} {doc['text']}")
            lexical_score = self._tfidf_score(query_terms, text_terms)
            vector_score = float(
                self.vector_index.embed_text(f"{doc['title']} {doc['text']}") @ query_vector
            )
            topic_score = self._topic_score(query_terms, doc.get("topics", []))
            trust_score = self._trust_score(doc.get("trust_level", "medium"))
            hybrid_score = lexical_score + 0.35 * vector_score + topic_score + trust_score
            if hybrid_score > 0:
                scored.append((hybrid_score, lexical_score, vector_score, doc))
        scored.sort(key=lambda item: (-item[0], item[3]["id"]))
        top_docs = scored[:5] if scored else [(0.1, 0.0, 0.0, doc) for doc in self.documents[:3]]
        return [
            SearchResult(
                source_id=doc["id"],
                title=doc["title"],
                snippet=self._best_snippet(doc["text"], query_terms),
                url=doc["url"],
                score=float(hybrid_score),
                text=doc["text"],
                lexical_score=float(lexical_score),
                vector_score=float(vector_score),
                hybrid_score=float(hybrid_score),
                source_type=doc.get("source_type", "local_note"),
                topics=doc.get("topics", []),
                trust_level=doc.get("trust_level", "medium"),
            )
            for hybrid_score, lexical_score, vector_score, doc in top_docs
        ]

    def _load_corpus(self, path: Path) -> list[dict[str, str]]:
        if not path.exists():
            return []
        docs = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                docs.append(json.loads(line))
        for doc in docs:
            doc.setdefault("source_type", self._infer_source_type(doc.get("url", "")))
            doc.setdefault("topics", self._infer_topics(doc))
            doc.setdefault("trust_level", "medium")
        return docs

    def _infer_source_type(self, url: str) -> str:
        if "/eval/" in url:
            return "evaluation_note"
        if "/trust/" in url:
            return "trust_note"
        if "/memory/" in url:
            return "memory_note"
        if "/agent/" in url:
            return "agent_note"
        return "local_note"

    def _infer_topics(self, doc: dict[str, str]) -> list[str]:
        text = f"{doc.get('id', '')} {doc.get('title', '')} {doc.get('url', '')}".lower()
        candidates = [
            "planner",
            "dag",
            "asyncio",
            "memory",
            "retrieval",
            "textrank",
            "citation",
            "hallucination",
            "redblue",
            "evaluation",
            "llm",
            "resume",
        ]
        return [topic for topic in candidates if topic in text]

    def _document_frequency(self, docs: list[dict[str, str]]) -> dict[str, int]:
        freq: dict[str, int] = {}
        for doc in docs:
            for token in set(self._tokens(f"{doc['title']} {doc['text']}")):
                freq[token] = freq.get(token, 0) + 1
        return freq

    def _tfidf_score(self, query_terms: list[str], text_terms: list[str]) -> float:
        if not query_terms or not text_terms:
            return 0.0
        n_docs = max(len(self.documents), 1)
        text_counts = {term: text_terms.count(term) for term in set(text_terms)}
        score = 0.0
        for term in query_terms:
            if term not in text_counts:
                continue
            idf = math.log((n_docs + 1) / (self.doc_freq.get(term, 0) + 1)) + 1
            score += text_counts[term] * idf
        return score / math.sqrt(len(text_terms))

    def _query_terms(self, text: str) -> list[str]:
        terms = self._tokens(text)
        normalized = text.lower()
        for cue, expansion in self.QUERY_EXPANSIONS.items():
            if cue in normalized:
                terms.extend(expansion)
        return list(dict.fromkeys(terms))

    def _topic_score(self, query_terms: list[str], topics: list[str] | None) -> float:
        if not topics:
            return 0.0
        query_set = set(query_terms)
        return 0.08 * sum(1 for topic in topics if topic in query_set)

    def _trust_score(self, trust_level: str) -> float:
        return {
            "high": 0.05,
            "medium": 0.0,
            "low": -0.05,
        }.get(trust_level, 0.0)

    def _best_snippet(self, text: str, query_terms: list[str]) -> str:
        sentences = re.split(r"(?<=[.!?。！？])\s+", text)
        ranked = sorted(
            sentences,
            key=lambda sentence: sum(1 for term in query_terms if term in self._tokens(sentence)),
            reverse=True,
        )
        return ranked[0].strip() if ranked and ranked[0].strip() else text[:240]

    def _tokens(self, text: str) -> list[str]:
        ascii_tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]+", text.lower())
        cjk_tokens = re.findall(r"[\u4e00-\u9fff]{2,}", text)
        return ascii_tokens + cjk_tokens
