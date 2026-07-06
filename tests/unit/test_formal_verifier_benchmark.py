from pathlib import Path

from deepresearch_agent.evaluation.verifier_benchmark import (
    aggregate_verifier_runs,
    benchmark_to_markdown,
    per_class_metrics,
    write_benchmark_outputs,
)


def test_per_class_metrics_from_confusion_matrix() -> None:
    confusion = {
        "supported": {"supported": 2, "partial": 1, "unsupported": 0, "contradicted": 0, "skipped": 0},
        "partial": {"supported": 1, "partial": 2, "unsupported": 0, "contradicted": 0, "skipped": 0},
        "unsupported": {"supported": 0, "partial": 0, "unsupported": 3, "contradicted": 0, "skipped": 0},
        "contradicted": {"supported": 0, "partial": 0, "unsupported": 0, "contradicted": 3, "skipped": 0},
    }

    metrics = per_class_metrics(confusion)

    assert metrics["supported"]["support"] == 3
    assert round(float(metrics["supported"]["precision"]), 3) == 0.667
    assert round(float(metrics["supported"]["recall"]), 3) == 0.667
    assert metrics["unsupported"]["f1"] == 1.0


def test_aggregate_verifier_runs_combines_repetitions() -> None:
    payloads = [_payload("run_a", 0.75), _payload("run_b", 0.75)]

    aggregate = aggregate_verifier_runs(payloads, latencies_seconds=[10.0, 14.0])

    assert aggregate["protocol"]["repetitions"] == 2
    assert aggregate["summary"]["total_attempted"] == 8
    assert aggregate["summary"]["total_correct"] == 6
    assert aggregate["summary"]["accuracy"] == 0.75
    assert aggregate["summary"]["latency_seconds_mean"] == 12.0
    assert aggregate["confusion_matrix"]["partial"]["unsupported"] == 2
    assert aggregate["per_class"]["partial"]["recall"] == 0.0
    assert aggregate["error_cases"]
    assert "Formal Verifier Benchmark" in benchmark_to_markdown(aggregate)


def test_write_benchmark_outputs(tmp_path: Path) -> None:
    aggregate = aggregate_verifier_runs([_payload("run_a", 0.75)])

    write_benchmark_outputs(aggregate, tmp_path)

    assert (tmp_path / "aggregate.json").exists()
    assert (tmp_path / "report.md").exists()
    assert "macro_f1" in (tmp_path / "report.md").read_text(encoding="utf-8")


def _payload(run_id: str, accuracy: float) -> dict:
    rows = [
        _row("a", "supported", "supported"),
        _row("b", "partial", "unsupported"),
        _row("c", "unsupported", "unsupported"),
        _row("d", "contradicted", "contradicted"),
    ]
    return {
        "summary": {
            "case_count": 4,
            "backend": "deepseek",
            "model": "deepseek-v4-flash",
            "run_real": True,
            "heuristic_accuracy": 0.25,
            "llm_attempted": 4,
            "llm_accuracy": accuracy,
            "llm_error_count": 1,
            "confusion_matrix": {
                "supported": {
                    "supported": 1,
                    "partial": 0,
                    "unsupported": 0,
                    "contradicted": 0,
                    "skipped": 0,
                },
                "partial": {
                    "supported": 0,
                    "partial": 0,
                    "unsupported": 1,
                    "contradicted": 0,
                    "skipped": 0,
                },
                "unsupported": {
                    "supported": 0,
                    "partial": 0,
                    "unsupported": 1,
                    "contradicted": 0,
                    "skipped": 0,
                },
                "contradicted": {
                    "supported": 0,
                    "partial": 0,
                    "unsupported": 0,
                    "contradicted": 1,
                    "skipped": 0,
                },
            },
            "total_tokens": 100,
            "estimated_cost_rmb": 0.01,
        },
        "rows": rows,
        "run_id": run_id,
    }


def _row(case_id: str, expected: str, actual: str) -> dict:
    return {
        "id": case_id,
        "claim": f"claim {case_id}",
        "expected_status": expected,
        "heuristic_status": "partial",
        "llm_status": actual,
        "llm_reason": "reason",
    }
