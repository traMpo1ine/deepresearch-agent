from deepresearch_agent.schemas import Evidence
from deepresearch_agent.source_observability import summarize_live_sources


def _external(source_id: str, url: str, provider: str, cache_hit: bool = False) -> Evidence:
    return Evidence(
        task_id="task_live",
        source_id=source_id,
        title=source_id,
        text="real source text",
        url=url,
        metadata={
            "provider": provider,
            "content_origin": f"{provider}_content",
            "fetch_status": "provider_content",
            "content_sha256": "a" * 64,
            "retrieved_at": "2026-07-16T00:00:00+00:00",
            "cache_hit": cache_hit,
            "risk_flags": [],
        },
    )


def test_live_source_summary_deduplicates_chunks_and_tracks_lineage() -> None:
    github = _external("github_repo", "https://github.com/org/repo", "github", cache_hit=True)
    duplicate_chunk = _external(
        "github_repo", "https://github.com/org/repo", "github", cache_hit=True
    )
    arxiv = _external("arxiv_paper", "https://arxiv.org/abs/1234", "arxiv")
    local = Evidence(
        task_id="task_local", source_id="local", title="Local", text="local", url="local://note"
    )

    summary = summarize_live_sources([github, duplicate_chunk, arxiv, local])

    assert summary.source_count == 2
    assert summary.provider_counts == {"arxiv": 1, "github": 1}
    assert summary.cache_hit_rate == 0.5
    assert summary.lineage_complete_rate == 1.0
    assert summary.duplicate_url_rate == 0.0
