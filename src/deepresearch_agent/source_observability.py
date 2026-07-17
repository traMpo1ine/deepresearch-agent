from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from deepresearch_agent.schemas import Evidence


@dataclass(slots=True)
class LiveSourceSummary:
    source_count: int
    provider_counts: dict[str, int]
    content_origin_counts: dict[str, int]
    fetch_status_counts: dict[str, int]
    cache_hit_count: int
    cache_hit_rate: float
    lineage_complete_count: int
    lineage_complete_rate: float
    risk_flag_source_count: int
    duplicate_url_rate: float

    def to_dict(self) -> dict[str, object]:
        return {
            "source_count": self.source_count,
            "provider_counts": self.provider_counts,
            "content_origin_counts": self.content_origin_counts,
            "fetch_status_counts": self.fetch_status_counts,
            "cache_hit_count": self.cache_hit_count,
            "cache_hit_rate": self.cache_hit_rate,
            "lineage_complete_count": self.lineage_complete_count,
            "lineage_complete_rate": self.lineage_complete_rate,
            "risk_flag_source_count": self.risk_flag_source_count,
            "duplicate_url_rate": self.duplicate_url_rate,
        }


def summarize_live_sources(evidence: list[Evidence]) -> LiveSourceSummary:
    sources: dict[str, Evidence] = {}
    for item in evidence:
        if item.url.startswith(("http://", "https://")):
            sources.setdefault(item.source_id, item)
    items = list(sources.values())
    count = len(items)
    provider_counts = Counter(str(item.metadata.get("provider", "unknown")) for item in items)
    origin_counts = Counter(
        str(item.metadata.get("content_origin", "unknown")) for item in items
    )
    fetch_counts = Counter(str(item.metadata.get("fetch_status", "unknown")) for item in items)
    cache_hit_count = sum(bool(item.metadata.get("cache_hit")) for item in items)
    lineage_complete_count = sum(_lineage_complete(item) for item in items)
    risk_count = sum(bool(item.metadata.get("risk_flags")) for item in items)
    unique_urls = {item.url.rstrip("/") for item in items}
    duplicate_url_rate = 0.0 if not count else 1.0 - len(unique_urls) / count
    return LiveSourceSummary(
        source_count=count,
        provider_counts=dict(sorted(provider_counts.items())),
        content_origin_counts=dict(sorted(origin_counts.items())),
        fetch_status_counts=dict(sorted(fetch_counts.items())),
        cache_hit_count=cache_hit_count,
        cache_hit_rate=round(cache_hit_count / count, 3) if count else 0.0,
        lineage_complete_count=lineage_complete_count,
        lineage_complete_rate=round(lineage_complete_count / count, 3) if count else 0.0,
        risk_flag_source_count=risk_count,
        duplicate_url_rate=round(max(0.0, duplicate_url_rate), 3),
    )


def _lineage_complete(item: Evidence) -> bool:
    required = ("provider", "content_origin", "fetch_status", "content_sha256", "retrieved_at")
    return all(item.metadata.get(key) not in (None, "") for key in required)
