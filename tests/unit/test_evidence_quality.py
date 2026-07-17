import pytest

from deepresearch_agent.evidence_quality import (
    annotate_source_quality,
    score_source_quality,
    suggest_follow_up_queries,
    summarize_source_quality,
)
from deepresearch_agent.schemas import Evidence


def _evidence(
    text: str = "SQLite memory stores traceable evidence for later inspection.",
    quote: str | None = "SQLite memory stores traceable evidence",
    score: float = 1.0,
    trust_level: str = "high",
) -> Evidence:
    return Evidence(
        task_id="task_test",
        title="Evidence quality",
        text=text,
        quote=quote,
        score=score,
        metadata={"trust_level": trust_level, "source_type": "trust_note"},
    )


def test_source_quality_prefers_quoted_trusted_evidence() -> None:
    strong = _evidence()
    weak = _evidence(text="short", quote=None, score=0.0, trust_level="low")

    strong_score, strong_signals = score_source_quality(strong)
    weak_score, _weak_signals = score_source_quality(weak)

    assert strong_score > weak_score
    assert strong_signals["quote_in_text"] is True
    assert annotate_source_quality(strong).metadata["source_quality_band"] == "high"


def test_source_quality_summary_and_follow_up_query() -> None:
    low_quality = [_evidence(text="short", quote=None, score=0.0, trust_level="low")]

    summary = summarize_source_quality(low_quality)
    queries = suggest_follow_up_queries(
        "Why verify claims?",
        low_quality,
        quality_threshold=0.9,
        max_queries=1,
    )

    assert summary.evidence_count == 1
    assert summary.low_quality_count == 1
    assert queries == ["Why verify claims? reliable evidence citation limitations"]


def test_source_quality_penalizes_prompt_injection_risk() -> None:
    clean = _evidence()
    risky = _evidence()
    risky.metadata["risk_flags"] = ["ignore_previous_instructions"]

    clean_score, _ = score_source_quality(clean)
    risky_score, signals = score_source_quality(risky)

    assert risky_score < clean_score
    assert signals["risk_flag_count"] == 1
    assert signals["quality_penalty"] >= 0.3


def test_follow_up_query_for_empty_evidence() -> None:
    assert suggest_follow_up_queries("Explain RAG", [], max_queries=1) == [
        "Explain RAG evidence citation source quote"
    ]


@pytest.mark.parametrize("max_queries", [0, -1])
def test_follow_up_query_can_be_disabled(max_queries: int) -> None:
    assert suggest_follow_up_queries("Explain RAG", [], max_queries=max_queries) == []
