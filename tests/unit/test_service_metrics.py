from concurrent.futures import ThreadPoolExecutor

from deepresearch_agent.web.metrics import ServiceMetrics


def test_service_metrics_renders_http_and_persisted_run_metrics() -> None:
    metrics = ServiceMetrics()
    metrics.observe_http("get", "/api/runs/{run_id}", 200, 0.125)
    metrics.observe_http("get", "/api/runs/{run_id}", 404, 0.025)

    payload = metrics.render(
        uptime_seconds=12.5,
        run_status_counts={"queued": 1, "running": 2, "succeeded": 4},
        max_active_runs=5,
    )

    assert 'route="/api/runs/{run_id}"' in payload
    assert 'status="200"} 1' in payload
    assert 'status="404"} 1' in payload
    assert 'deepresearch_demo_runs{status="succeeded"} 4' in payload
    assert "deepresearch_demo_run_active 3" in payload
    assert "deepresearch_demo_run_capacity 5" in payload


def test_service_metrics_counter_updates_are_thread_safe() -> None:
    metrics = ServiceMetrics()

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(
            pool.map(
                lambda _: metrics.observe_http("POST", "/api/runs", 202, 0.01),
                range(200),
            )
        )

    payload = metrics.render(
        uptime_seconds=1.0,
        run_status_counts={},
        max_active_runs=2,
    )
    assert 'method="POST",route="/api/runs",status="202"} 200' in payload
    assert 'method="POST",route="/api/runs"} 200' in payload
