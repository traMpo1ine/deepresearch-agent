from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


VERIFIER_STATUSES = ["supported", "partial", "unsupported", "contradicted"]


def aggregate_verifier_runs(
    payloads: list[dict[str, Any]],
    latencies_seconds: list[float] | None = None,
) -> dict[str, Any]:
    if not payloads:
        raise ValueError("At least one verifier payload is required.")
    latencies = latencies_seconds or [0.0 for _ in payloads]
    summaries = [payload["summary"] for payload in payloads]
    combined_confusion = _empty_confusion()
    for summary in summaries:
        combined_confusion = add_confusion_matrices(
            combined_confusion,
            summary.get("confusion_matrix", {}),
        )
    per_class = per_class_metrics(combined_confusion)
    macro = macro_metrics(per_class)
    accuracies = [
        float(summary["llm_accuracy"])
        for summary in summaries
        if summary.get("llm_accuracy") is not None
    ]
    heuristic_accuracies = [float(summary.get("heuristic_accuracy", 0.0)) for summary in summaries]
    total_attempted = sum(int(summary.get("llm_attempted", 0)) for summary in summaries)
    total_correct = sum(
        int(summary.get("llm_attempted", 0)) - int(summary.get("llm_error_count", 0))
        for summary in summaries
    )
    total_tokens = sum(int(summary.get("total_tokens", 0)) for summary in summaries)
    total_cost = sum(float(summary.get("estimated_cost_rmb", 0.0)) for summary in summaries)
    return {
        "protocol": {
            "dataset": "synthetic_balanced_verifier",
            "repetitions": len(payloads),
            "case_count_per_repetition": int(summaries[0].get("case_count", 0)),
            "status_labels": list(VERIFIER_STATUSES),
            "judge": summaries[0].get("backend"),
            "model": summaries[0].get("model"),
            "run_real": bool(summaries[0].get("run_real", False)),
            "boundary": (
                "Formal verifier benchmark for claim/evidence classification; not an end-to-end "
                "DeepResearch benchmark and not a production factuality guarantee."
            ),
        },
        "summary": {
            "total_cases": sum(int(summary.get("case_count", 0)) for summary in summaries),
            "total_attempted": total_attempted,
            "total_correct": total_correct,
            "accuracy": total_correct / total_attempted if total_attempted else 0.0,
            "accuracy_mean": mean(accuracies),
            "accuracy_std": sample_std(accuracies),
            "heuristic_accuracy_mean": mean(heuristic_accuracies),
            "heuristic_accuracy_std": sample_std(heuristic_accuracies),
            "macro_precision": macro["precision"],
            "macro_recall": macro["recall"],
            "macro_f1": macro["f1"],
            "total_tokens": total_tokens,
            "estimated_cost_rmb": round(total_cost, 8),
            "latency_seconds_mean": mean(latencies),
            "latency_seconds_std": sample_std(latencies),
        },
        "per_class": per_class,
        "confusion_matrix": combined_confusion,
        "repetitions": [
            {
                "index": index,
                "llm_accuracy": summary.get("llm_accuracy"),
                "llm_error_count": summary.get("llm_error_count"),
                "total_tokens": summary.get("total_tokens"),
                "estimated_cost_rmb": summary.get("estimated_cost_rmb"),
                "latency_seconds": latencies[index - 1] if index - 1 < len(latencies) else 0.0,
            }
            for index, summary in enumerate(summaries, start=1)
        ],
        "error_cases": collect_error_cases(payloads),
    }


def add_confusion_matrices(
    left: dict[str, dict[str, int]],
    right: dict[str, dict[str, int]],
) -> dict[str, dict[str, int]]:
    result = _empty_confusion()
    actual_labels = [*VERIFIER_STATUSES, "skipped"]
    for expected in VERIFIER_STATUSES:
        for actual in actual_labels:
            result[expected][actual] = int(left.get(expected, {}).get(actual, 0)) + int(
                right.get(expected, {}).get(actual, 0)
            )
    return result


def per_class_metrics(confusion: dict[str, dict[str, int]]) -> dict[str, dict[str, float | int]]:
    metrics: dict[str, dict[str, float | int]] = {}
    for label in VERIFIER_STATUSES:
        tp = int(confusion.get(label, {}).get(label, 0))
        support = sum(int(value) for actual, value in confusion.get(label, {}).items() if actual != "skipped")
        predicted = sum(
            int(confusion.get(expected, {}).get(label, 0))
            for expected in VERIFIER_STATUSES
        )
        precision = tp / predicted if predicted else 0.0
        recall = tp / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        metrics[label] = {
            "support": support,
            "predicted": predicted,
            "true_positive": tp,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    return metrics


def macro_metrics(per_class: dict[str, dict[str, float | int]]) -> dict[str, float]:
    return {
        "precision": mean([float(item["precision"]) for item in per_class.values()]),
        "recall": mean([float(item["recall"]) for item in per_class.values()]),
        "f1": mean([float(item["f1"]) for item in per_class.values()]),
    }


def collect_error_cases(payloads: list[dict[str, Any]], limit: int = 60) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for run_index, payload in enumerate(payloads, start=1):
        for row in payload.get("rows", []):
            if row.get("llm_status") in {None, "skipped", row.get("expected_status")}:
                continue
            key = (str(row.get("id")), str(row.get("expected_status")), str(row.get("llm_status")))
            if key in seen:
                continue
            seen.add(key)
            errors.append(
                {
                    "run_index": run_index,
                    "id": row.get("id"),
                    "expected_status": row.get("expected_status"),
                    "heuristic_status": row.get("heuristic_status"),
                    "llm_status": row.get("llm_status"),
                    "claim": row.get("claim"),
                    "llm_reason": row.get("llm_reason"),
                }
            )
            if len(errors) >= limit:
                return errors
    return errors


def benchmark_to_markdown(payload: dict[str, Any]) -> str:
    protocol = payload["protocol"]
    summary = payload["summary"]
    lines = [
        "# Formal Verifier Benchmark",
        "",
        "## Protocol",
        "",
        f"- dataset: `{protocol['dataset']}`",
        f"- repetitions: `{protocol['repetitions']}`",
        f"- case_count_per_repetition: `{protocol['case_count_per_repetition']}`",
        f"- judge: `{protocol['judge']}`",
        f"- model: `{protocol['model']}`",
        f"- run_real: `{str(protocol['run_real']).lower()}`",
        f"- boundary: {protocol['boundary']}",
        "",
        "## Summary",
        "",
        f"- total_cases: `{summary['total_cases']}`",
        f"- total_attempted: `{summary['total_attempted']}`",
        f"- accuracy: `{summary['accuracy']:.3f}`",
        f"- accuracy_mean: `{summary['accuracy_mean']:.3f}`",
        f"- accuracy_std: `{summary['accuracy_std']:.3f}`",
        f"- heuristic_accuracy_mean: `{summary['heuristic_accuracy_mean']:.3f}`",
        f"- macro_precision: `{summary['macro_precision']:.3f}`",
        f"- macro_recall: `{summary['macro_recall']:.3f}`",
        f"- macro_f1: `{summary['macro_f1']:.3f}`",
        f"- total_tokens: `{summary['total_tokens']}`",
        f"- estimated_cost_rmb: `{summary['estimated_cost_rmb']}`",
        f"- latency_seconds_mean: `{summary['latency_seconds_mean']:.3f}`",
        "",
        "## Per-Class Metrics",
        "",
        "| class | support | predicted | precision | recall | f1 |",
        "| --- | ---:| ---:| ---:| ---:| ---:|",
    ]
    for label, item in payload["per_class"].items():
        lines.append(
            f"| {label} | {item['support']} | {item['predicted']} | "
            f"{float(item['precision']):.3f} | {float(item['recall']):.3f} | {float(item['f1']):.3f} |"
        )
    lines.extend(
        [
            "",
            "## Confusion Matrix",
            "",
            "| expected \\ predicted | supported | partial | unsupported | contradicted | skipped |",
            "| --- | ---:| ---:| ---:| ---:| ---:|",
        ]
    )
    for expected, counts in payload["confusion_matrix"].items():
        lines.append(
            "| {expected} | {supported} | {partial} | {unsupported} | {contradicted} | {skipped} |".format(
                expected=expected,
                supported=counts.get("supported", 0),
                partial=counts.get("partial", 0),
                unsupported=counts.get("unsupported", 0),
                contradicted=counts.get("contradicted", 0),
                skipped=counts.get("skipped", 0),
            )
        )
    lines.extend(["", "## Repetitions", ""])
    for run in payload["repetitions"]:
        lines.append(
            "- run {index}: accuracy={llm_accuracy}, errors={llm_error_count}, "
            "tokens={total_tokens}, cost_rmb={estimated_cost_rmb}, latency={latency_seconds:.3f}s".format(
                **run
            )
        )
    lines.extend(["", "## Error Cases", ""])
    if not payload["error_cases"]:
        lines.append("- No LLM errors recorded.")
    for error in payload["error_cases"][:30]:
        lines.append(
            "- run `{run_index}` `{id}` expected={expected_status} "
            "heuristic={heuristic_status} llm={llm_status}: {claim}".format(**error)
        )
    return "\n".join(lines)


def write_benchmark_outputs(payload: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "aggregate.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "report.md").write_text(benchmark_to_markdown(payload), encoding="utf-8")


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def sample_std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    value_mean = mean(values)
    variance = sum((value - value_mean) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def _empty_confusion() -> dict[str, dict[str, int]]:
    return {
        expected: {actual: 0 for actual in [*VERIFIER_STATUSES, "skipped"]}
        for expected in VERIFIER_STATUSES
    }
