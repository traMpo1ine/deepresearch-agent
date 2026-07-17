import asyncio
import json
import logging
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from deepresearch_agent.web import app as web_app
from deepresearch_agent.web.worker import DemoRunWorker


def test_web_health_and_static_page() -> None:
    client = TestClient(web_app.app)

    health = client.get("/api/health")
    page = client.get("/")

    assert health.status_code == 200
    assert health.json()["default_backend"] == "mock"
    assert health.json()["corpus_profiles"]
    assert health.json()["web_search"]["providers"]
    assert health.json()["run_store"]["backend"] == "sqlite_wal"
    assert page.status_code == 200
    assert "DeepResearch Agent Demo" in page.text
    assert "Read real external data" in page.text


def test_health_probes_and_request_observability(caplog) -> None:
    client = TestClient(web_app.create_app())
    caplog.set_level(logging.INFO, logger="deepresearch_agent.access")

    live = client.get("/api/health/live", headers={"X-Request-ID": "req-test-123"})
    ready = client.get("/api/health/ready")
    metrics = client.get("/metrics")

    assert live.status_code == 200
    assert live.json()["status"] == "alive"
    assert live.headers["X-Request-ID"] == "req-test-123"
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"
    assert metrics.status_code == 200
    assert metrics.headers["content-type"].startswith("text/plain")
    assert 'route="/api/health/live"' in metrics.text
    assert "deepresearch_demo_run_capacity 2" in metrics.text
    access_events = [json.loads(record.message) for record in caplog.records]
    assert any(
        event["request_id"] == "req-test-123"
        and event["path"] == "/api/health/live"
        and event["status_code"] == 200
        for event in access_events
    )


def test_invalid_request_id_is_replaced() -> None:
    client = TestClient(web_app.create_app())

    response = client.get("/api/health/live", headers={"X-Request-ID": "bad id with spaces"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"].startswith("req_")


def test_web_lists_corpus_profiles() -> None:
    client = TestClient(web_app.app)

    response = client.get("/api/corpus-profiles")
    profiles = response.json()["profiles"]

    assert response.status_code == 200
    assert {profile["key"] for profile in profiles} >= {
        "offline_agent_docs",
        "resume_agent_docs",
        "local_kb_docs",
    }


def test_default_showcase_returns_clear_error_when_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(web_app, "DEFAULT_SHOWCASE_CANDIDATES", (tmp_path / "missing",))
    client = TestClient(web_app.create_app())

    response = client.get("/api/showcase/default")

    assert response.status_code == 404
    assert "No default showcase artifacts" in response.json()["detail"]["message"]


def test_default_showcase_artifacts_are_structured(tmp_path, monkeypatch) -> None:
    showcase_dir = _write_showcase(tmp_path / "showcase")
    monkeypatch.setattr(web_app, "DEFAULT_SHOWCASE_CANDIDATES", (showcase_dir,))
    client = TestClient(web_app.create_app())

    response = client.get("/api/showcase/default")
    payload = response.json()

    assert response.status_code == 200
    assert payload["overview"]["run_id"] == "run_demo"
    assert payload["plan"]["tasks"]
    assert payload["report"]["claims"]
    assert payload["evidence"][0]["quote"] == "quote"
    assert "Verifier" in payload["verification"]["markdown"]


def test_repository_default_showcase_is_real_deepseek() -> None:
    client = TestClient(web_app.app)

    response = client.get("/api/showcase/default")
    payload = response.json()

    assert response.status_code == 200
    assert payload["showcase_dir"].replace("\\", "/") == "reports/golden_demo/deepseek_v3"
    assert payload["overview"]["backend"] == "deepseek"
    assert payload["overview"]["writer_mode"] == "llm"
    assert payload["overview"]["writer_fallback"] is False
    assert payload["overview"]["llm_total_tokens"] > 0
    assert "real DeepSeek Writer" in payload["overview"]["boundary"]
    assert "https://" not in payload["overview"]["question"]


def test_mock_run_generates_artifacts_with_background_job(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(web_app, "DEMO_RUNS_DIR", tmp_path / "demo_runs")
    received = {}

    async def fake_build_showcase(**kwargs):
        received.update(kwargs)
        _write_showcase(Path(kwargs["output_dir"]))
        return SimpleNamespace(output_dir=Path(kwargs["output_dir"]), run_id="run_demo")

    monkeypatch.setattr(web_app, "build_showcase", fake_build_showcase)
    client = TestClient(web_app.create_app())

    request_payload = {
        "question": "Why verify citations?",
        "backend": "mock",
        "repair_rounds": 2,
        "corpus_profile": "resume_agent_docs",
        "enable_web_search": True,
        "web_search_provider": "wikipedia,arxiv",
        "max_web_results": 4,
    }
    response = client.post(
        "/api/runs",
        headers={"X-Request-ID": "portfolio-run-1", "Idempotency-Key": "portfolio-op-1"},
        json=request_payload,
    )
    run_id = response.json()["run_id"]
    status = client.get(f"/api/runs/{run_id}").json()
    artifacts = client.get(f"/api/runs/{run_id}/artifacts")
    run_list = client.get("/api/runs?status=succeeded")
    restarted_client = TestClient(
        web_app.create_app(run_store_path=tmp_path / "demo_runs" / "run_registry.sqlite3")
    )
    persisted = restarted_client.get(f"/api/runs/{run_id}")
    replay = client.post(
        "/api/runs",
        headers={"Idempotency-Key": "portfolio-op-1"},
        json=request_payload,
    )
    conflict = client.post(
        "/api/runs",
        headers={"Idempotency-Key": "portfolio-op-1"},
        json={**request_payload, "question": "A different research request"},
    )

    assert response.status_code == 202
    assert status["status"] == "succeeded"
    assert status["request_id"] == "portfolio-run-1"
    assert status["corpus_profile"] == "resume_agent_docs"
    assert "resume_agent_docs" in str(received["corpus_path"])
    assert received["enable_web_search"] is True
    assert received["web_search_provider"] == "wikipedia,arxiv"
    assert received["use_iterative_search"] is True
    assert artifacts.status_code == 200
    assert artifacts.json()["report"]["claims"]
    assert any(item["run_id"] == run_id for item in run_list.json()["runs"])
    assert persisted.status_code == 200
    assert persisted.json()["status"] == "succeeded"
    assert replay.json()["run_id"] == run_id
    assert replay.status_code == 200
    assert replay.headers["X-Idempotent-Replay"] == "true"
    assert conflict.status_code == 409
    assert "different request payload" in conflict.json()["detail"]


def test_worker_execution_mode_leaves_job_queued_for_standalone_worker(tmp_path) -> None:
    application = web_app.create_app(
        run_store_path=tmp_path / "runs.sqlite3",
        execution_mode="worker",
    )
    client = TestClient(application)
    response = client.post(
        "/api/runs",
        json={"question": "Why use a standalone worker?", "backend": "mock"},
    )
    run_id = response.json()["run_id"]

    assert response.status_code == 202
    assert response.json()["status"] == "queued"
    assert client.get("/api/health").json()["run_store"]["execution_mode"] == "worker"

    executed: list[str] = []

    async def fake_executor(job) -> None:
        executed.append(job.run_id)

    worker = DemoRunWorker(
        application.state.run_store,
        worker_id="integration-worker",
        executor=fake_executor,
    )
    asyncio.run(worker.run_once())
    finished = client.get(f"/api/runs/{run_id}").json()

    assert executed == [run_id]
    assert finished["status"] == "succeeded"
    assert finished["worker_id"] == "integration-worker"
    assert finished["attempt_count"] == 1


def test_mock_run_rejects_unsafe_idempotency_key(tmp_path) -> None:
    client = TestClient(web_app.create_app(run_store_path=tmp_path / "runs.sqlite3"))

    response = client.post(
        "/api/runs",
        headers={"Idempotency-Key": "unsafe key with spaces"},
        json={"question": "Why verify citations?", "backend": "mock"},
    )

    assert response.status_code == 400
    assert "Idempotency-Key" in response.json()["detail"]


def test_mock_run_rejects_real_backend() -> None:
    client = TestClient(web_app.app)

    response = client.post(
        "/api/runs",
        json={"question": "Why verify citations?", "backend": "deepseek"},
    )

    assert response.status_code == 400
    assert "only allow backend='mock'" in response.json()["detail"]


def test_uploaded_document_builds_corpus_and_runs_after_restart(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(web_app, "DEMO_RUNS_DIR", tmp_path / "demo_runs")
    received = {}

    async def fake_build_showcase(**kwargs):
        received.update(kwargs)
        _write_showcase(Path(kwargs["output_dir"]))
        return SimpleNamespace(output_dir=Path(kwargs["output_dir"]), run_id="run_upload")

    monkeypatch.setattr(web_app, "build_showcase", fake_build_showcase)
    store_path = tmp_path / "demo_runs" / "run_registry.sqlite3"
    upload_root = tmp_path / "uploads"
    client = TestClient(
        web_app.create_app(run_store_path=store_path, upload_root=upload_root)
    )

    uploaded = client.post(
        "/api/corpora/uploads",
        files={
            "file": (
                "real_agent_note.md",
                b"# Real Agent Note\n\nUploaded citation evidence supports a grounded answer.",
                "text/markdown",
            )
        },
    )
    upload_payload = uploaded.json()
    duplicate = client.post(
        "/api/corpora/uploads",
        files={
            "file": (
                "same_content.md",
                b"# Real Agent Note\n\nUploaded citation evidence supports a grounded answer.",
                "text/markdown",
            )
        },
    )
    response = client.post(
        "/api/runs",
        headers={"Idempotency-Key": "uploaded-corpus-run"},
        json={
            "question": "What evidence was uploaded?",
            "backend": "mock",
            "uploaded_corpus_id": upload_payload["corpus_id"],
        },
    )

    assert uploaded.status_code == 201
    assert upload_payload["chunk_count"] >= 1
    assert duplicate.status_code == 200
    assert duplicate.json()["deduplicated"] is True
    assert response.status_code == 202
    assert response.json()["corpus_profile"].startswith("upload:")
    assert Path(received["corpus_path"]).is_file()
    restarted = TestClient(
        web_app.create_app(run_store_path=store_path, upload_root=upload_root)
    )
    detail = restarted.get(f"/api/corpora/uploads/{upload_payload['corpus_id']}")
    assert detail.status_code == 200
    assert detail.json()["content_sha256"] == upload_payload["content_sha256"]


def test_upload_api_enforces_size_and_format_limits(tmp_path) -> None:
    client = TestClient(
        web_app.create_app(
            run_store_path=tmp_path / "runs.sqlite3",
            upload_root=tmp_path / "uploads",
            max_upload_bytes=1024,
        )
    )

    too_large = client.post(
        "/api/corpora/uploads",
        files={"file": ("large.txt", b"a" * 1025, "text/plain")},
    )
    unsupported = client.post(
        "/api/corpora/uploads",
        files={"file": ("image.png", b"png", "image/png")},
    )

    assert too_large.status_code == 413
    assert unsupported.status_code == 400


def test_deepseek_showcase_dry_run_does_not_require_key(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    client = TestClient(web_app.app)

    response = client.post("/api/deepseek-showcase", json={"run_real": False})

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert "Dry run" in response.json()["error"]


def _write_showcase(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    report = {
        "question": "Why verify citations?",
        "title": "Demo Report",
        "summary": "summary",
        "run_id": "run_demo",
        "claims": [
            {
                "id": "claim_1",
                "text": "Claims need citations.",
                "citation_ids": ["ev_1"],
                "verification_status": "supported",
            }
        ],
        "evidence": [
            {
                "id": "ev_1",
                "title": "Evidence",
                "quote": "quote",
                "text": "text",
                "source_id": "local",
                "score": 1.0,
            }
        ],
        "repair_actions": [],
        "repair_loop_trace": [],
    }
    files = {
        "index.md": "# Index",
        "plan.md": "\n".join(
            [
                "# Plan",
                "### task_1",
                "- type: root",
                "- dependencies: none",
                "- question: Why verify citations?",
                "```mermaid",
                "flowchart TD",
                'task_1["root"]',
                "```",
            ]
        ),
        "report.md": "# Demo Report",
        "report.json": json.dumps(report),
        "run_summary.json": json.dumps(
            {
                "run_id": "run_demo",
                "llm_backend": "mock",
                "model": "mock-researcher-v0",
                "task_count": 1,
                "evidence_count": 1,
                "repair_count": 0,
            }
        ),
        "memory_trace.md": "# Memory",
        "compression_trace.md": "# Compression",
        "verifier_trace.md": "# Verifier",
        "redblue_trace.md": "# RedBlue",
        "eval_summary.md": "# Eval",
        "llm_backend.md": "# Backend",
    }
    for name, text in files.items():
        (path / name).write_text(text, encoding="utf-8")
    return path
