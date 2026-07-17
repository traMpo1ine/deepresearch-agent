from __future__ import annotations

from collections import defaultdict
from threading import Lock


class ServiceMetrics:
    """Small dependency-free Prometheus collector with bounded route labels."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._request_counts: dict[tuple[str, str, int], int] = defaultdict(int)
        self._duration_sums: dict[tuple[str, str], float] = defaultdict(float)
        self._duration_counts: dict[tuple[str, str], int] = defaultdict(int)

    def observe_http(
        self,
        method: str,
        route: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        safe_method = method.upper()[:16]
        safe_route = route if route.startswith("/") else "/__unmatched__"
        with self._lock:
            self._request_counts[(safe_method, safe_route, status_code)] += 1
            self._duration_sums[(safe_method, safe_route)] += max(0.0, duration_seconds)
            self._duration_counts[(safe_method, safe_route)] += 1

    def render(
        self,
        *,
        uptime_seconds: float,
        run_status_counts: dict[str, int],
        max_active_runs: int,
    ) -> str:
        with self._lock:
            request_counts = dict(self._request_counts)
            duration_sums = dict(self._duration_sums)
            duration_counts = dict(self._duration_counts)
        lines = [
            "# HELP deepresearch_process_uptime_seconds Process uptime in seconds.",
            "# TYPE deepresearch_process_uptime_seconds gauge",
            f"deepresearch_process_uptime_seconds {max(0.0, uptime_seconds):.6f}",
            "# HELP deepresearch_http_requests_total HTTP requests by method, route and status.",
            "# TYPE deepresearch_http_requests_total counter",
        ]
        for (method, route, status), count in sorted(request_counts.items()):
            lines.append(
                "deepresearch_http_requests_total"
                f'{{method="{_escape(method)}",route="{_escape(route)}",status="{status}"}} '
                f"{count}"
            )
        lines.extend(
            [
                "# HELP deepresearch_http_request_duration_seconds_sum "
                "Accumulated HTTP request latency.",
                "# TYPE deepresearch_http_request_duration_seconds_sum counter",
            ]
        )
        for (method, route), value in sorted(duration_sums.items()):
            labels = f'method="{_escape(method)}",route="{_escape(route)}"'
            lines.append(
                f"deepresearch_http_request_duration_seconds_sum{{{labels}}} {value:.6f}"
            )
        lines.extend(
            [
                "# HELP deepresearch_http_request_duration_seconds_count "
                "Observed HTTP requests for latency aggregation.",
                "# TYPE deepresearch_http_request_duration_seconds_count counter",
            ]
        )
        for (method, route), count in sorted(duration_counts.items()):
            labels = f'method="{_escape(method)}",route="{_escape(route)}"'
            lines.append(f"deepresearch_http_request_duration_seconds_count{{{labels}}} {count}")
        lines.extend(
            [
                "# HELP deepresearch_demo_runs Current persisted demo runs by status.",
                "# TYPE deepresearch_demo_runs gauge",
            ]
        )
        for status in ("queued", "running", "succeeded", "failed"):
            lines.append(
                f'deepresearch_demo_runs{{status="{status}"}} '
                f"{int(run_status_counts.get(status, 0))}"
            )
        active = int(run_status_counts.get("queued", 0)) + int(
            run_status_counts.get("running", 0)
        )
        lines.extend(
            [
                "# HELP deepresearch_demo_run_active Current queued and running demo runs.",
                "# TYPE deepresearch_demo_run_active gauge",
                f"deepresearch_demo_run_active {active}",
                "# HELP deepresearch_demo_run_capacity Configured active run capacity.",
                "# TYPE deepresearch_demo_run_capacity gauge",
                f"deepresearch_demo_run_capacity {max(1, max_active_runs)}",
            ]
        )
        return "\n".join(lines) + "\n"


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
