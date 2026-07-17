from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from deepresearch_agent.agents.searcher import SearcherAgent
from deepresearch_agent.evaluation.retrieval import (
    all_relevant_at_k,
    evaluate_searcher,
    hit_at_k,
    load_retrieval_cases,
    ndcg_at_k,
    recall_at_k,
    reciprocal_rank,
    validate_relevance_labels,
)


def test_retrieval_metrics_support_multiple_relevance_labels() -> None:
    ranked = ["noise", "gold_a", "gold_b"]
    relevant = ["gold_a", "gold_b"]

    assert recall_at_k(ranked, relevant, 2) == 0.5
    assert hit_at_k(ranked, relevant, 1) == 0.0
    assert hit_at_k(ranked, relevant, 2) == 1.0
    assert all_relevant_at_k(ranked, relevant, 2) == 0.0
    assert all_relevant_at_k(ranked, relevant, 3) == 1.0
    assert reciprocal_rank(ranked, relevant, 3) == 0.5
    assert ndcg_at_k(["gold_a", "gold_b"], relevant, 2) == pytest.approx(1.0)


def test_load_and_validate_retrieval_cases(tmp_path) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_text(
        json.dumps(
            {
                "id": "case_1",
                "question": "Where is alpha?",
                "required_sources": ["alpha"],
                "difficulty": "easy",
                "domain": "test",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    cases = load_retrieval_cases(path)

    assert cases[0].relevant_source_ids == ("alpha",)
    validate_relevance_labels(cases, ["alpha"])
    with pytest.raises(ValueError, match="alpha"):
        validate_relevance_labels(cases, ["beta"])


@pytest.mark.asyncio
async def test_evaluate_searcher_reports_failures_and_breakdowns(tmp_path) -> None:
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "alpha",
                        "title": "Alpha storage",
                        "text": "alpha durable storage",
                        "url": "local://alpha",
                    }
                ),
                json.dumps(
                    {
                        "id": "beta",
                        "title": "Beta queue",
                        "text": "beta task queue",
                        "url": "local://beta",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    cases_path = tmp_path / "cases.jsonl"
    cases_path.write_text(
        json.dumps(
            {
                "id": "case_1",
                "question": "alpha storage",
                "required_sources": ["alpha"],
                "difficulty": "easy",
                "domain": "storage",
                "required_hops": 1,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    cases = load_retrieval_cases(cases_path)
    searcher = SearcherAgent(corpus_path=corpus, retrieval_mode="lexical", result_limit=1)

    evaluation = await evaluate_searcher(searcher, cases, ks=(1,))

    assert evaluation["summary"]["recall_at_1"] == 1.0
    assert evaluation["summary"]["mrr_at_1"] == 1.0
    assert evaluation["breakdowns"]["domain"]["storage"]["case_count"] == 1.0
    assert evaluation["failures_at_max_k"] == []


def test_searcher_retrieval_mode_validation() -> None:
    with pytest.raises(ValueError, match="retrieval_mode"):
        SearcherAgent(retrieval_mode="unknown")
    with pytest.raises(ValueError, match="result_limit"):
        SearcherAgent(result_limit=0)


def test_frozen_retrieval_holdout_has_expected_coverage() -> None:
    path = Path("data/benchmarks/retrieval_holdout_v1.jsonl")
    cases = load_retrieval_cases(path)
    corpus_ids = {
        json.loads(line)["id"]
        for line in Path("data/corpus/offline_corpus.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }

    assert len(cases) == 80
    assert len({case.case_id for case in cases}) == 80
    assert {case.language for case in cases} == {"zh", "en"}
    assert len({case.query_style for case in cases}) >= 8
    assert max(case.required_hops for case in cases) >= 4
    assert sum(case.required_hops > 1 for case in cases) >= 35
    assert Counter(case.language for case in cases)["zh"] >= 45
    validate_relevance_labels(cases, corpus_ids)
