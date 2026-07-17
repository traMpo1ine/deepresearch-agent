from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from deepresearch_agent.agents.base import BaseAgent
from deepresearch_agent.memory import EmbeddingProvider, NumpyVectorIndex
from deepresearch_agent.schemas import ResearchTask
from deepresearch_agent.tools.web_search import (
    WebSearchProvider,
    create_web_search_provider,
    provider_telemetry,
)


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
    metadata: dict[str, object] | None = None


class SearcherAgent(BaseAgent):
    name = "searcher"
    RETRIEVAL_MODES = frozenset({"lexical", "vector", "hybrid"})
    HYBRID_VECTOR_WEIGHT = 0.20
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

    def __init__(
        self,
        corpus_path: str | Path = "data/corpus/offline_corpus.jsonl",
        enable_web_search: bool = False,
        web_search_provider: str = "disabled",
        max_web_results: int = 3,
        web_search_cache_path: str | Path | None = None,
        web_search_cache_ttl_seconds: int = 3600,
        web_search_cache_backend: str = "sqlite",
        web_search_redis_url: str | None = None,
        provider: WebSearchProvider | None = None,
        retrieval_mode: str = "hybrid",
        result_limit: int = 5,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        if retrieval_mode not in self.RETRIEVAL_MODES:
            supported = ", ".join(sorted(self.RETRIEVAL_MODES))
            raise ValueError(f"retrieval_mode must be one of: {supported}")
        if result_limit < 1:
            raise ValueError("result_limit must be at least 1")
        self.corpus_path = Path(corpus_path)
        self.documents = self._load_corpus(self.corpus_path)
        self.doc_freq = self._document_frequency(self.documents)
        self.vector_index = NumpyVectorIndex(dim=64)
        self.enable_web_search = enable_web_search
        self.web_search_provider_name = web_search_provider
        self.max_web_results = max_web_results
        self.retrieval_mode = retrieval_mode
        self.result_limit = result_limit
        self.embedding_provider = embedding_provider
        self.web_search_provider = provider or create_web_search_provider(
            web_search_provider,
            cache_path=web_search_cache_path,
            cache_ttl_seconds=web_search_cache_ttl_seconds,
            cache_backend=web_search_cache_backend,
            redis_url=web_search_redis_url,
        )

    async def _run(self, agent_input: object, context=None) -> list[SearchResult]:
        if not isinstance(agent_input, ResearchTask):
            raise TypeError("SearcherAgent.run expects a ResearchTask.")
        return await self.search(agent_input)

    async def search(self, task: ResearchTask) -> list[SearchResult]:
        query_terms = self._query_terms(task.question)
        documents = list(self.documents)
        web_docs = await self._web_documents(task.question)
        documents.extend(web_docs)
        scored: list[tuple[float, float, float, float, float, dict[str, object]]] = []
        vector_scores = await self._vector_scores(query_terms, documents)
        for doc, vector_score in zip(documents, vector_scores, strict=True):
            text_terms = self._tokens(f"{doc['title']} {doc['text']}")
            lexical_score = self._tfidf_score(query_terms, text_terms)
            topic_score = self._topic_score(query_terms, doc.get("topics", []))
            trust_score = self._trust_score(doc.get("trust_level", "medium"))
            # Source trust is deliberately not added to relevance. A trusted but unrelated
            # document must not enter the candidate set; trust is only a deterministic tie-breaker.
            hybrid_score = (
                lexical_score + self.HYBRID_VECTOR_WEIGHT * vector_score + topic_score
            )
            rank_score = self._rank_score(lexical_score, vector_score, hybrid_score)
            if rank_score > 0:
                scored.append(
                    (rank_score, lexical_score, vector_score, hybrid_score, trust_score, doc)
                )
        scored.sort(key=lambda item: (-item[0], -item[4], item[5]["id"]))
        top_docs = (
            self._select_top_docs(scored, web_docs, limit=self.result_limit)
            if scored
            else [(0.1, 0.0, 0.0, 0.0, 0.0, doc) for doc in documents[: self.result_limit]]
        )
        return [
            SearchResult(
                source_id=doc["id"],
                title=doc["title"],
                snippet=self._best_snippet(doc["text"], query_terms),
                url=doc["url"],
                score=float(rank_score),
                text=doc["text"],
                lexical_score=float(lexical_score),
                vector_score=float(vector_score),
                hybrid_score=float(hybrid_score),
                source_type=doc.get("source_type", "local_note"),
                topics=doc.get("topics", []),
                trust_level=doc.get("trust_level", "medium"),
                metadata=doc.get("metadata", {}),
            )
            for rank_score, lexical_score, vector_score, hybrid_score, _, doc in top_docs
        ]

    async def _web_documents(self, query: str) -> list[dict[str, object]]:
        if not self.enable_web_search:
            return []
        web_query = self._web_query(query)
        results = await self.web_search_provider.search(
            web_query,
            max_results=self.max_web_results,
        )
        documents: list[dict[str, object]] = []
        for result in results:
            url_digest = hashlib.sha1(result.url.encode("utf-8")).hexdigest()[:12]
            documents.append(
                {
                    "id": f"web_{result.provider}_{url_digest}",
                    "title": result.title,
                    "text": result.content,
                    "url": result.url,
                    "source_type": result.source_type,
                    "topics": ["web", "search"],
                    "trust_level": result.trust_level,
                    "provider": result.provider,
                    "provider_score": result.score,
                    "metadata": {
                        **result.metadata,
                        "provider": result.provider,
                        "provider_score": result.score,
                        "web_query": web_query,
                    },
                }
            )
        return documents

    def web_search_telemetry(self) -> dict[str, object]:
        """Expose transport health without leaking provider credentials or full queries."""
        return provider_telemetry(self.web_search_provider)

    def embedding_telemetry(self) -> dict[str, object]:
        if self.embedding_provider is None:
            return {
                "provider": "hashing",
                "dimensions": self.vector_index.dim,
                "offline_safe": True,
            }
        return self.embedding_provider.status()

    async def _vector_scores(
        self,
        query_terms: list[str],
        documents: list[dict[str, object]],
    ) -> list[float]:
        if self.retrieval_mode == "lexical":
            return [0.0] * len(documents)
        query_text = " ".join(query_terms)
        document_texts = [f"{doc['title']} {doc['text']}" for doc in documents]
        if self.embedding_provider is None:
            query_vector = self.vector_index.embed_text(query_text)
            return [
                float(self.vector_index.embed_text(text) @ query_vector)
                for text in document_texts
            ]
        vectors = await self.embedding_provider.embed_many([query_text, *document_texts])
        matrix = np.asarray(vectors, dtype=np.float32)
        if matrix.ndim != 2 or matrix.shape[0] != len(documents) + 1:
            raise RuntimeError("embedding provider returned an invalid matrix")
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        if np.any(norms == 0) or not np.isfinite(matrix).all():
            raise RuntimeError("embedding provider returned invalid vectors")
        normalized = matrix / norms
        return (normalized[1:] @ normalized[0]).astype(float).tolist()

    def _web_query(self, task_question: str) -> str:
        """Remove planner scaffolding before sending a query to external search APIs."""
        candidate = task_question.strip()
        # Explicit URLs are user-selected sources, not planner prose. Preserve the
        # whole question so DirectURLProvider can extract every source deterministically.
        if re.search(r"https?://", candidate):
            return candidate
        for marker in (" for: ", " for：", "："):
            if marker in candidate:
                suffix = candidate.rsplit(marker, maxsplit=1)[-1].strip()
                if suffix:
                    candidate = suffix
                    break
        for cue in ("为什么", "如何", "怎么", "是否", "有哪些", "有什么"):
            if cue in candidate:
                prefix = candidate.split(cue, maxsplit=1)[0].strip(" ，,。！？?")
                if prefix:
                    candidate = prefix
                break
        leading_phrase = re.match(
            r"^([A-Za-z][A-Za-z0-9_-]*(?:\s+[A-Za-z][A-Za-z0-9_-]*)+)",
            candidate,
        )
        return leading_phrase.group(1) if leading_phrase else candidate

    def _select_top_docs(
        self,
        scored: list[tuple[float, float, float, float, float, dict[str, object]]],
        web_docs: list[dict[str, object]],
        limit: int,
    ) -> list[tuple[float, float, float, float, float, dict[str, object]]]:
        selected = scored[:limit]
        if not web_docs or any(item[5].get("url", "").startswith("http") for item in selected):
            return selected
        web_ids = {doc["id"] for doc in web_docs}
        best_web = next(
            (
                item
                for item in scored
                if item[5]["id"] in web_ids and (item[1] > 0 or item[2] >= 0.2)
            ),
            None,
        )
        if best_web is None:
            return selected
        if len(selected) < limit:
            return [*selected, best_web]
        return [*selected[:-1], best_web]

    def _rank_score(
        self,
        lexical_score: float,
        vector_score: float,
        hybrid_score: float,
    ) -> float:
        if self.retrieval_mode == "lexical":
            return lexical_score
        if self.retrieval_mode == "vector":
            return vector_score
        return hybrid_score

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
