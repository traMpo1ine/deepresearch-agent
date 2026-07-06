import json
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from deepresearch_agent.web import app as web_app


def test_web_health_and_static_page() -> None:
    client = TestClient(web_app.app)

    health = client.get("/api/health")
    page = client.get("/")

    assert health.status_code == 200
    assert health.json()["default_backend"] == "mock"
    assert health.json()["corpus_profiles"]
    assert page.status_code == 200
    assert "DeepResearch Agent Demo" in page.text


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


def test_mock_run_generates_artifacts_with_background_job(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(web_app, "DEMO_RUNS_DIR", tmp_path / "demo_runs")
    monkeypatch.setattr(web_app, "RUNS", {})
    received = {}

    async def fake_build_showcase(**kwargs):
        received.update(kwargs)
        _write_showcase(Path(kwargs["output_dir"]))
        return SimpleNamespace(output_dir=Path(kwargs["output_dir"]), run_id="run_demo")

    monkeypatch.setattr(web_app, "build_showcase", fake_build_showcase)
    client = TestClient(web_app.create_app())

    response = client.post(
        "/api/runs",
        json={
            "question": "Why verify citations?",
            "backend": "mock",
            "repair_rounds": 2,
            "corpus_profile": "resume_agent_docs",
        },
    )
    run_id = response.json()["run_id"]
    status = client.get(f"/api/runs/{run_id}").json()
    artifacts = client.get(f"/api/runs/{run_id}/artifacts")

    assert response.status_code == 200
    assert status["status"] == "succeeded"
    assert status["corpus_profile"] == "resume_agent_docs"
    assert "resume_agent_docs" in str(received["corpus_path"])
    assert artifacts.status_code == 200
    assert artifacts.json()["report"]["claims"]


def test_mock_run_rejects_real_backend() -> None:
    client = TestClient(web_app.app)

    response = client.post(
        "/api/runs",
        json={"question": "Why verify citations?", "backend": "deepseek"},
    )

    assert response.status_code == 400
    assert "only allow backend='mock'" in response.json()["detail"]


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
