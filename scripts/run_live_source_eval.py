from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.tools.web_search import (  # noqa: E402
    create_web_search_provider,
    provider_telemetry,
)


@dataclass(slots=True)
class LiveCaseResult:
    case_id: str
    provider: str
    query: str
    success: bool
    result_count: int
    first_latency_seconds: float
    cached_latency_seconds: float
    cache_hit_rate: float
    lineage_complete_rate: float
    transport_telemetry_complete_rate: float
    valid_url_rate: float
    max_content_chars: int
    expected_title_match: bool
    provider_event_count: int
    provider_retry_count: int
    provider_circuit_open_count: int
    cache_error_types: list[str]
    titles: list[str]
    urls: list[str]
    failures: list[str]


async def evaluate_case(case: dict, cache_path: Path) -> LiveCaseResult:
    provider_name = str(case["provider"])
    query = str(case["query"])
    max_results = max(1, int(case.get("max_results", 3)))
    provider = create_web_search_provider(
        provider_name,
        cache_path=cache_path,
        cache_ttl_seconds=3600,
    )
    started = time.perf_counter()
    first = await provider.search(query, max_results=max_results)
    first_latency = time.perf_counter() - started
    started = time.perf_counter()
    cached = await provider.search(query, max_results=max_results)
    cached_latency = time.perf_counter() - started
    results = first or cached
    result_count = len(results)
    cache_hits = sum(bool(result.metadata.get("cache_hit")) for result in cached)
    lineage_complete = sum(_lineage_complete(result.metadata) for result in results)
    telemetry_complete = sum(_transport_telemetry_complete(result.metadata) for result in results)
    expected_domain = str(case.get("expected_domain", ""))
    valid_urls = sum(_valid_url(result.url, expected_domain) for result in results)
    max_content_chars = max((len(result.content) for result in results), default=0)
    expected_title = str(case.get("expected_title_contains", "")).lower()
    expected_title_match = not expected_title or any(
        expected_title in result.title.lower() for result in results
    )
    failures = []
    if result_count < int(case.get("min_results", 1)):
        failures.append("insufficient_results")
    if max_content_chars < int(case.get("min_content_chars", 80)):
        failures.append("content_too_short")
    if results and valid_urls != result_count:
        failures.append("invalid_or_unexpected_url")
    if results and lineage_complete != result_count:
        failures.append("incomplete_lineage")
    if results and telemetry_complete != result_count:
        failures.append("incomplete_transport_telemetry")
    if cached and cache_hits != len(cached):
        failures.append("cache_miss_on_second_pass")
    if not expected_title_match:
        failures.append("expected_title_not_found_in_top_k")
    telemetry_summary = provider_telemetry(provider)["summary"]
    cache_error_types = sorted(
        {
            str(result.metadata["cache_error"])
            for result in results
            if result.metadata.get("cache_error")
        }
    )
    return LiveCaseResult(
        case_id=str(case["id"]),
        provider=provider_name,
        query=query,
        success=not failures,
        result_count=result_count,
        first_latency_seconds=round(first_latency, 4),
        cached_latency_seconds=round(cached_latency, 4),
        cache_hit_rate=round(cache_hits / len(cached), 3) if cached else 0.0,
        lineage_complete_rate=(
            round(lineage_complete / result_count, 3) if result_count else 0.0
        ),
        transport_telemetry_complete_rate=(
            round(telemetry_complete / result_count, 3) if result_count else 0.0
        ),
        valid_url_rate=round(valid_urls / result_count, 3) if result_count else 0.0,
        max_content_chars=max_content_chars,
        expected_title_match=expected_title_match,
        provider_event_count=int(telemetry_summary["event_count"]),
        provider_retry_count=int(telemetry_summary["total_retries"]),
        provider_circuit_open_count=int(telemetry_summary["circuit_open_count"]),
        cache_error_types=cache_error_types,
        titles=[result.title for result in results],
        urls=[result.url for result in results],
        failures=failures,
    )


async def run(dataset: Path, output_dir: Path) -> dict:
    cases = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line]
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_path = output_dir / "live_source_cache.sqlite3"
    results = []
    for case in cases:
        results.append(await evaluate_case(case, cache_path))
    success_count = sum(result.success for result in results)
    payload = {
        "dataset": str(dataset),
        "generated_at": datetime.now().astimezone().isoformat(),
        "case_count": len(results),
        "success_count": success_count,
        "success_rate": round(success_count / len(results), 3) if results else 0.0,
        "mean_cache_hit_rate": round(
            sum(result.cache_hit_rate for result in results) / len(results), 3
        )
        if results
        else 0.0,
        "mean_lineage_complete_rate": round(
            sum(result.lineage_complete_rate for result in results) / len(results), 3
        )
        if results
        else 0.0,
        "mean_transport_telemetry_complete_rate": round(
            sum(result.transport_telemetry_complete_rate for result in results) / len(results), 3
        )
        if results
        else 0.0,
        "cases": [asdict(result) for result in results],
    }
    (output_dir / "metrics.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "report.md").write_text(_to_markdown(payload), encoding="utf-8")
    return payload


def _lineage_complete(metadata: dict[str, object]) -> bool:
    keys = ("content_origin", "fetch_status", "content_sha256", "retrieved_at")
    return all(metadata.get(key) not in (None, "") for key in keys)


def _transport_telemetry_complete(metadata: dict[str, object]) -> bool:
    keys = (
        "provider_attempts",
        "provider_retries",
        "provider_latency_seconds",
        "provider_circuit_state",
    )
    return all(metadata.get(key) is not None for key in keys)


def _valid_url(url: str, expected_domain: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    return not expected_domain or expected_domain in parsed.hostname


def _to_markdown(payload: dict) -> str:
    lines = [
        "# Live Source Evaluation",
        "",
        f"- success_rate: `{payload['success_rate']:.3f}`",
        f"- mean_cache_hit_rate: `{payload['mean_cache_hit_rate']:.3f}`",
        f"- mean_lineage_complete_rate: `{payload['mean_lineage_complete_rate']:.3f}`",
        "- mean_transport_telemetry_complete_rate: "
        f"`{payload['mean_transport_telemetry_complete_rate']:.3f}`",
        "",
        "| Case | Provider | Success | Results | Telemetry | Retries | First latency | Cached latency | Failures |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in payload["cases"]:
        lines.append(
            f"| {item['case_id']} | {item['provider']} | {item['success']} | "
            f"{item['result_count']} | {item['transport_telemetry_complete_rate']:.3f} | "
            f"{item['provider_retry_count']} | "
            f"{item['first_latency_seconds']:.4f}s | "
            f"{item['cached_latency_seconds']:.4f}s | {', '.join(item['failures']) or '-'} |"
        )
    lines.extend(["", "## URLs", ""])
    for item in payload["cases"]:
        lines.append(f"### {item['case_id']}")
        lines.extend(f"- {url}" for url in item["urls"])
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate real external data providers and cache.")
    parser.add_argument("--dataset", default="data/benchmarks/live_source_cases.jsonl")
    parser.add_argument("--output-dir")
    parser.add_argument("--fail-on-error", action="store_true")
    args = parser.parse_args()
    output_dir = Path(args.output_dir) if args.output_dir else Path(
        "reports/live_source_eval"
    ) / datetime.now().strftime("%Y%m%d_%H%M%S")
    payload = asyncio.run(run(Path(args.dataset), output_dir))
    print(f"Live source evaluation: {payload['success_count']}/{payload['case_count']} passed")
    print(f"Report: {output_dir / 'report.md'}")
    if args.fail_on_error and payload["success_rate"] < 1.0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
