from __future__ import annotations

import re

import numpy as np

from deepresearch_agent.memory.vector_index import NumpyVectorIndex
from deepresearch_agent.schemas import CompressedContext, CompressedSentence, Evidence


class TextRankCompressor:
    def __init__(self, vector_dim: int = 64) -> None:
        self.vector_index = NumpyVectorIndex(dim=vector_dim)

    def compress(self, text: str, max_sentences: int = 5) -> str:
        sentences = self._split_sentences(text)
        if len(sentences) <= max_sentences:
            return text
        scores = self._textrank_scores(sentences)
        selected = sorted(range(len(sentences)), key=lambda i: scores[i], reverse=True)[:max_sentences]
        selected.sort()
        return " ".join(sentences[i] for i in selected)

    def compress_evidence(
        self,
        question: str,
        evidence: list[Evidence],
        max_sentences: int = 12,
        l1_top_k: int = 16,
    ) -> CompressedContext:
        candidates: list[tuple[Evidence, str, bool]] = []
        for item in evidence:
            for sentence in self._split_sentences(item.text):
                candidates.append((item, sentence, item.quote is not None and item.quote in sentence))
            if item.quote:
                candidates.append((item, item.quote, True))

        original_char_count = sum(len(item.text) for item in evidence)
        if not candidates:
            return CompressedContext(question, [], original_char_count, 0)

        query_vector = self.vector_index.embed_text(question)
        l1_scored = []
        for item, sentence, preserved in candidates:
            score = float(self.vector_index.embed_text(sentence) @ query_vector)
            if preserved:
                score += 0.25
            l1_scored.append((score, item, sentence, preserved))
        l1_scored.sort(key=lambda row: row[0], reverse=True)
        narrowed = l1_scored[: min(l1_top_k, len(l1_scored))]

        sentences = [row[2] for row in narrowed]
        rank_scores = self._textrank_scores(sentences)
        final_rows = []
        for index, (l1_score, item, sentence, preserved) in enumerate(narrowed):
            final_rows.append((l1_score + rank_scores[index] + (0.5 if preserved else 0.0), item, sentence, preserved))
        final_rows.sort(key=lambda row: row[0], reverse=True)

        selected: dict[tuple[str, str], CompressedSentence] = {}
        for score, item, sentence, preserved in final_rows:
            key = (item.id, sentence)
            if key not in selected:
                selected[key] = CompressedSentence(
                    text=sentence,
                    evidence_id=item.id,
                    source_id=item.source_id,
                    score=float(score),
                    preserved_quote=preserved,
                )
            if len(selected) >= max_sentences:
                break

        for item in evidence:
            if item.quote and (item.id, item.quote) not in selected:
                selected[(item.id, item.quote)] = CompressedSentence(
                    text=item.quote,
                    evidence_id=item.id,
                    source_id=item.source_id,
                    score=1.0,
                    preserved_quote=True,
                )

        sentences_out = list(selected.values())
        compressed_char_count = sum(len(sentence.text) for sentence in sentences_out)
        return CompressedContext(
            question=question,
            sentences=sentences_out,
            original_char_count=original_char_count,
            compressed_char_count=compressed_char_count,
        )

    def _split_sentences(self, text: str) -> list[str]:
        return [sentence.strip() for sentence in re.split(r"(?<=[.!?。！？])\s+", text) if sentence.strip()]

    def _textrank_scores(self, sentences: list[str], damping: float = 0.85, iterations: int = 30) -> np.ndarray:
        if not sentences:
            return np.array([], dtype=np.float32)
        vectors = np.vstack([self.vector_index.embed_text(sentence) for sentence in sentences])
        similarity = vectors @ vectors.T
        np.fill_diagonal(similarity, 0.0)
        row_sums = similarity.sum(axis=1, keepdims=True)
        graph = np.divide(similarity, row_sums, out=np.zeros_like(similarity), where=row_sums != 0)
        scores = np.ones(len(sentences), dtype=np.float32) / len(sentences)
        teleport = (1.0 - damping) / len(sentences)
        for _ in range(iterations):
            scores = teleport + damping * graph.T @ scores
        return scores
