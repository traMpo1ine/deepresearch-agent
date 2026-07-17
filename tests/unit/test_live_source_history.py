from pathlib import Path

from deepresearch_agent.live_source_history import (
    append_live_source_snapshot,
    build_live_source_snapshot,
    live_source_history_markdown,
)


def _metrics(success_rate: float = 1.0) -> dict:
    return {
        "dataset": "data/benchmarks/live_source_cases.jsonl",
        "generated_at": "2026-07-17T08:00:00+08:00",
        "case_count": 2,
        "success_count": int(success_rate * 2),
        "success_rate": success_rate,
        "mean_cache_hit_rate": 1.0,
        "mean_lineage_complete_rate": 1.0,
        "mean_transport_telemetry_complete_rate": 1.0,
        "cases": [
            {
                "case_id": "wiki",
                "provider": "wikipedia",
                "success": True,
                "first_latency_seconds": 1.0,
                "cached_latency_seconds": 0.01,
                "provider_retry_count": 0,
                "provider_circuit_open_count": 0,
                "failures": [],
            },
            {
                "case_id": "github",
                "provider": "github",
                "success": success_rate == 1.0,
                "first_latency_seconds": 3.0,
                "cached_latency_seconds": 0.02,
                "provider_retry_count": 1,
                "provider_circuit_open_count": 0,
                "failures": [] if success_rate == 1.0 else ["insufficient_results"],
            },
        ],
    }


def test_live_source_snapshot_summarizes_latency_retries_and_failures() -> None:
    snapshot = build_live_source_snapshot(_metrics(0.5), run_id="123")

    assert snapshot["run_id"] == "123"
    assert snapshot["provider_counts"] == {"wikipedia": 1, "github": 1}
    assert snapshot["mean_first_latency_seconds"] == 2.0
    assert snapshot["p95_first_latency_seconds"] == 3.0
    assert snapshot["provider_retry_count"] == 1
    assert snapshot["failure_cases"][0]["case_id"] == "github"


def test_live_source_history_append_is_atomic_and_deduplicated(tmp_path: Path) -> None:
    path = tmp_path / "history" / "history.jsonl"
    snapshot = build_live_source_snapshot(_metrics(), run_id="123")

    first = append_live_source_snapshot(path, snapshot)
    second = append_live_source_snapshot(path, snapshot)

    assert len(first) == 1
    assert len(second) == 1
    assert path.exists()
    assert not path.with_name("history.jsonl.tmp").exists()


def test_live_source_history_markdown_reports_observation_rates() -> None:
    passed = build_live_source_snapshot(_metrics(), run_id="one")
    failed_metrics = _metrics(0.5)
    failed_metrics["generated_at"] = "2026-07-24T08:00:00+08:00"
    failed = build_live_source_snapshot(failed_metrics, run_id="two")

    markdown = live_source_history_markdown([passed, failed])

    assert "observations: `2`" in markdown
    assert "full_pass_rate: `0.500`" in markdown
    assert "minimum_success_rate: `0.500`" in markdown
    assert "| 2026-07-24T08:00:00+08:00 | two | 0.500 |" in markdown
