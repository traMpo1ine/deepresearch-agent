from __future__ import annotations

from dataclasses import dataclass

from deepresearch_agent.schemas import Evidence


@dataclass(slots=True)
class SourceQualitySummary:
    evidence_count: int
    mean_quality: float
    high_quality_count: int
    low_quality_count: int
    quote_coverage: float

    def to_dict(self) -> dict:
        return {
            "evidence_count": self.evidence_count,
            "mean_quality": self.mean_quality,
            "high_quality_count": self.high_quality_count,
            "low_quality_count": self.low_quality_count,
            "quote_coverage": self.quote_coverage,
        }


def score_source_quality(evidence: Evidence) -> tuple[float, dict[str, float | str | bool]]:
    """Score how useful a source chunk is for citation-grounded generation."""
    trust_level = str(evidence.metadata.get("trust_level", "medium"))
    source_type = str(evidence.metadata.get("source_type", "local_note"))
    quote = evidence.quote or ""
    text = evidence.text or ""
    content_origin = str(evidence.metadata.get("content_origin", "local_or_unknown"))
    fetch_status = str(evidence.metadata.get("fetch_status", "not_applicable"))
    risk_flags = evidence.metadata.get("risk_flags", [])
    if not isinstance(risk_flags, list):
        risk_flags = []

    trust_score = {"high": 0.25, "medium": 0.17, "low": 0.06}.get(trust_level, 0.12)
    quote_score = 0.25 if quote and quote in text else 0.15 if quote else 0.0
    length_score = _length_score(len(text))
    retrieval_score = min(max(float(evidence.score), 0.0) / 4.0, 0.2)
    source_type_score = 0.12 if source_type != "local_note" else 0.08
    lineage_score = 0.06 if evidence.metadata.get("content_sha256") else 0.0
    snippet_penalty = 0.08 if content_origin.endswith("snippet") else 0.0
    fetch_penalty = 0.08 if fetch_status in {"fetch_exception", "network_error"} else 0.0
    risk_penalty = min(0.5, 0.3 * len(risk_flags))

    total = min(
        trust_score
        + quote_score
        + length_score
        + retrieval_score
        + source_type_score
        + lineage_score
        - snippet_penalty
        - fetch_penalty
        - risk_penalty,
        1.0,
    )
    total = max(total, 0.0)
    signals: dict[str, float | str | bool] = {
        "trust_level": trust_level,
        "source_type": source_type,
        "has_quote": bool(quote),
        "quote_in_text": bool(quote and quote in text),
        "trust_score": round(trust_score, 3),
        "quote_score": round(quote_score, 3),
        "length_score": round(length_score, 3),
        "retrieval_score": round(retrieval_score, 3),
        "source_type_score": round(source_type_score, 3),
        "content_origin": content_origin,
        "fetch_status": fetch_status,
        "has_content_hash": bool(evidence.metadata.get("content_sha256")),
        "risk_flag_count": len(risk_flags),
        "lineage_score": round(lineage_score, 3),
        "quality_penalty": round(snippet_penalty + fetch_penalty + risk_penalty, 3),
    }
    return round(total, 3), signals


def annotate_source_quality(evidence: Evidence) -> Evidence:
    quality, signals = score_source_quality(evidence)
    evidence.metadata["source_quality"] = quality
    evidence.metadata["source_quality_signals"] = signals
    evidence.metadata["source_quality_band"] = (
        "high" if quality >= 0.75 else "medium" if quality >= 0.5 else "low"
    )
    return evidence


def summarize_source_quality(evidence: list[Evidence]) -> SourceQualitySummary:
    if not evidence:
        return SourceQualitySummary(
            evidence_count=0,
            mean_quality=0.0,
            high_quality_count=0,
            low_quality_count=0,
            quote_coverage=0.0,
        )
    qualities = [_quality(item) for item in evidence]
    quote_count = sum(1 for item in evidence if item.quote)
    return SourceQualitySummary(
        evidence_count=len(evidence),
        mean_quality=round(sum(qualities) / len(qualities), 3),
        high_quality_count=sum(1 for score in qualities if score >= 0.75),
        low_quality_count=sum(1 for score in qualities if score < 0.5),
        quote_coverage=round(quote_count / len(evidence), 3),
    )


def suggest_follow_up_queries(
    question: str,
    evidence: list[Evidence],
    quality_threshold: float = 0.58,
    max_queries: int = 1,
) -> list[str]:
    summary = summarize_source_quality(evidence)
    if max_queries <= 0:
        return []
    if summary.evidence_count == 0:
        return [_clean_query(f"{question} evidence citation source quote")]
    if summary.mean_quality < quality_threshold:
        return [_clean_query(f"{question} reliable evidence citation limitations")]
    if summary.quote_coverage < 0.8:
        return [_clean_query(f"{question} exact quote source citation")]
    return []


def _quality(evidence: Evidence) -> float:
    existing = evidence.metadata.get("source_quality")
    if isinstance(existing, (int, float)):
        return float(existing)
    quality, _signals = score_source_quality(evidence)
    return quality


def _length_score(length: int) -> float:
    if length >= 160:
        return 0.18
    if length >= 80:
        return 0.12
    if length > 0:
        return 0.05
    return 0.0


def _clean_query(query: str) -> str:
    return " ".join(query.split())
