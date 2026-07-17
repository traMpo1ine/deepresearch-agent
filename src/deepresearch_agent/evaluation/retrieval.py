from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Iterable

from deepresearch_agent.agents.searcher import SearcherAgent
from deepresearch_agent.schemas import ResearchTask


@dataclass(frozen=True, slots=True)
class RetrievalCase:
    case_id: str
    question: str
    relevant_source_ids: tuple[str, ...]
    difficulty: str = "unknown"
    domain: str = "unknown"
    required_hops: int = 1
    language: str = "unknown"
    query_style: str = "unknown"


def load_retrieval_cases(path: str | Path) -> list[RetrievalCase]:
    cases: list[RetrievalCase] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        payload = json.loads(line)
        source_ids = tuple(dict.fromkeys(payload.get("required_sources", [])))
        if not payload.get("id") or not payload.get("question") or not source_ids:
            raise ValueError(f"invalid retrieval case at line {line_number}")
        cases.append(
            RetrievalCase(
                case_id=str(payload["id"]),
                question=str(payload["question"]),
                relevant_source_ids=source_ids,
                difficulty=str(payload.get("difficulty", "unknown")),
                domain=str(payload.get("domain", "unknown")),
                required_hops=int(payload.get("required_hops", len(source_ids))),
                language=str(payload.get("language", "unknown")),
                query_style=str(payload.get("query_style", "unknown")),
            )
        )
    if not cases:
        raise ValueError("retrieval benchmark must contain at least one case")
    case_ids = [case.case_id for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("retrieval benchmark case ids must be unique")
    return cases


def validate_relevance_labels(
    cases: Iterable[RetrievalCase], corpus_source_ids: Iterable[str]
) -> None:
    corpus_ids = set(corpus_source_ids)
    missing = sorted(
        {
            source_id
            for case in cases
            for source_id in case.relevant_source_ids
            if source_id not in corpus_ids
        }
    )
    if missing:
        raise ValueError(f"relevance labels missing from corpus: {', '.join(missing)}")


def recall_at_k(ranked_ids: list[str], relevant_ids: Iterable[str], k: int) -> float:
    relevant = set(relevant_ids)
    if not relevant:
        return 0.0
    return len(relevant.intersection(ranked_ids[:k])) / len(relevant)


def hit_at_k(ranked_ids: list[str], relevant_ids: Iterable[str], k: int) -> float:
    return float(bool(set(relevant_ids).intersection(ranked_ids[:k])))


def all_relevant_at_k(ranked_ids: list[str], relevant_ids: Iterable[str], k: int) -> float:
    relevant = set(relevant_ids)
    return float(bool(relevant) and relevant.issubset(ranked_ids[:k]))


def reciprocal_rank(ranked_ids: list[str], relevant_ids: Iterable[str], k: int) -> float:
    relevant = set(relevant_ids)
    for rank, source_id in enumerate(ranked_ids[:k], 1):
        if source_id in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(ranked_ids: list[str], relevant_ids: Iterable[str], k: int) -> float:
    relevant = set(relevant_ids)
    if not relevant:
        return 0.0
    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, source_id in enumerate(ranked_ids[:k], 1)
        if source_id in relevant
    )
    ideal_count = min(len(relevant), k)
    ideal_dcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_count + 1))
    return dcg / ideal_dcg


def _aggregate(case_results: list[dict[str, object]], ks: tuple[int, ...]) -> dict[str, float]:
    metrics: dict[str, float] = {"case_count": float(len(case_results))}
    for k in ks:
        for metric in ("recall", "hit_rate", "all_relevant", "ndcg"):
            key = f"{metric}_at_{k}"
            metrics[key] = mean(float(result[key]) for result in case_results)
    max_k = max(ks)
    metrics[f"mrr_at_{max_k}"] = mean(
        float(result[f"reciprocal_rank_at_{max_k}"]) for result in case_results
    )
    return metrics


async def evaluate_searcher(
    searcher: SearcherAgent,
    cases: list[RetrievalCase],
    ks: tuple[int, ...] = (1, 3, 5),
) -> dict[str, object]:
    if not ks or any(k < 1 for k in ks):
        raise ValueError("ks must contain positive integers")
    ks = tuple(sorted(set(ks)))
    max_k = max(ks)
    case_results: list[dict[str, object]] = []

    for case in cases:
        results = await searcher.search(ResearchTask(question=case.question))
        ranked_ids = [result.source_id for result in results]
        result: dict[str, object] = {
            **asdict(case),
            "relevant_source_ids": list(case.relevant_source_ids),
            "retrieved_source_ids": ranked_ids[:max_k],
            "missing_source_ids_at_max_k": sorted(
                set(case.relevant_source_ids).difference(ranked_ids[:max_k])
            ),
        }
        for k in ks:
            result[f"recall_at_{k}"] = recall_at_k(ranked_ids, case.relevant_source_ids, k)
            result[f"hit_rate_at_{k}"] = hit_at_k(ranked_ids, case.relevant_source_ids, k)
            result[f"all_relevant_at_{k}"] = all_relevant_at_k(
                ranked_ids, case.relevant_source_ids, k
            )
            result[f"ndcg_at_{k}"] = ndcg_at_k(ranked_ids, case.relevant_source_ids, k)
        result[f"reciprocal_rank_at_{max_k}"] = reciprocal_rank(
            ranked_ids, case.relevant_source_ids, max_k
        )
        case_results.append(result)

    grouped: dict[str, dict[str, dict[str, float]]] = {}
    for field in ("difficulty", "domain", "required_hops", "language", "query_style"):
        grouped[field] = {}
        values = sorted({str(result[field]) for result in case_results})
        for value in values:
            subset = [result for result in case_results if str(result[field]) == value]
            grouped[field][value] = _aggregate(subset, ks)

    return {
        "retrieval_mode": searcher.retrieval_mode,
        "ks": list(ks),
        "summary": _aggregate(case_results, ks),
        "breakdowns": grouped,
        "failures_at_max_k": [
            result for result in case_results if result["missing_source_ids_at_max_k"]
        ],
        "case_results": case_results,
    }
