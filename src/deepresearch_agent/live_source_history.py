from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def build_live_source_snapshot(metrics: dict[str, Any], run_id: str | None = None) -> dict[str, Any]:
    cases = [case for case in metrics.get("cases", []) if isinstance(case, dict)]
    first_latencies = [float(case.get("first_latency_seconds") or 0.0) for case in cases]
    cached_latencies = [float(case.get("cached_latency_seconds") or 0.0) for case in cases]
    provider_counts: dict[str, int] = {}
    for case in cases:
        provider = str(case.get("provider") or "unknown")
        provider_counts[provider] = provider_counts.get(provider, 0) + 1
    failure_cases = [
        {
            "case_id": str(case.get("case_id") or "unknown"),
            "provider": str(case.get("provider") or "unknown"),
            "failures": [str(item) for item in case.get("failures", [])],
        }
        for case in cases
        if not bool(case.get("success"))
    ]
    return {
        "schema_version": 1,
        "run_id": run_id,
        "generated_at": str(metrics.get("generated_at") or ""),
        "dataset": str(metrics.get("dataset") or ""),
        "case_count": int(metrics.get("case_count") or len(cases)),
        "success_count": int(metrics.get("success_count") or 0),
        "success_rate": float(metrics.get("success_rate") or 0.0),
        "mean_cache_hit_rate": float(metrics.get("mean_cache_hit_rate") or 0.0),
        "mean_lineage_complete_rate": float(
            metrics.get("mean_lineage_complete_rate") or 0.0
        ),
        "mean_transport_telemetry_complete_rate": float(
            metrics.get("mean_transport_telemetry_complete_rate") or 0.0
        ),
        "mean_first_latency_seconds": _mean(first_latencies),
        "p95_first_latency_seconds": _percentile(first_latencies, 0.95),
        "mean_cached_latency_seconds": _mean(cached_latencies),
        "provider_counts": provider_counts,
        "provider_retry_count": sum(
            int(case.get("provider_retry_count") or 0) for case in cases
        ),
        "provider_circuit_open_count": sum(
            int(case.get("provider_circuit_open_count") or 0) for case in cases
        ),
        "failure_cases": failure_cases,
    }


def append_live_source_snapshot(path: Path, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    history = load_live_source_history(path)
    identity = (snapshot.get("run_id"), snapshot.get("generated_at"))
    if not any((item.get("run_id"), item.get("generated_at")) == identity for item in history):
        history.append(snapshot)
    history.sort(key=lambda item: str(item.get("generated_at") or ""))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in history) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return history


def load_live_source_history(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def live_source_history_markdown(history: list[dict[str, Any]]) -> str:
    observations = len(history)
    full_passes = sum(float(item.get("success_rate") or 0.0) == 1.0 for item in history)
    success_rates = [float(item.get("success_rate") or 0.0) for item in history]
    latest = history[-1] if history else {}
    lines = [
        "# Live Source History",
        "",
        f"- observations: `{observations}`",
        f"- full_pass_rate: `{full_passes / observations:.3f}`" if observations else "- full_pass_rate: `0.000`",
        f"- mean_success_rate: `{_mean(success_rates):.3f}`",
        f"- minimum_success_rate: `{min(success_rates, default=0.0):.3f}`",
        f"- latest_success_rate: `{float(latest.get('success_rate') or 0.0):.3f}`",
        "",
        "| Generated at | Run | Success | Cache | Lineage | Telemetry | Mean first | P95 first | Retries | Failed cases |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in history[-30:]:
        lines.append(
            f"| {item.get('generated_at') or '-'} | {item.get('run_id') or '-'} | "
            f"{float(item.get('success_rate') or 0.0):.3f} | "
            f"{float(item.get('mean_cache_hit_rate') or 0.0):.3f} | "
            f"{float(item.get('mean_lineage_complete_rate') or 0.0):.3f} | "
            f"{float(item.get('mean_transport_telemetry_complete_rate') or 0.0):.3f} | "
            f"{float(item.get('mean_first_latency_seconds') or 0.0):.3f}s | "
            f"{float(item.get('p95_first_latency_seconds') or 0.0):.3f}s | "
            f"{int(item.get('provider_retry_count') or 0)} | "
            f"{len(item.get('failure_cases') or [])} |"
        )
    lines.extend(
        [
            "",
            "The history is an external-dependency observation series, not a production SLA.",
            "GitHub cache/artifact retention and runner network conditions affect continuity.",
        ]
    )
    return "\n".join(lines) + "\n"


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(quantile * len(ordered)) - 1))
    return round(ordered[index], 4)
