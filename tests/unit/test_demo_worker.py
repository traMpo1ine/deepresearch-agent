from __future__ import annotations

from pathlib import Path

import pytest

from deepresearch_agent.web.run_store import DemoRun, DemoRunStore
from deepresearch_agent.web.worker import DemoRunWorker


def _run(run_id: str) -> DemoRun:
    return DemoRun(
        run_id=run_id,
        question="Why use a durable worker?",
        backend="mock",
        model=None,
        repair_rounds=2,
        corpus_profile="offline_agent_docs",
        corpus_path=Path("data/corpus/offline_corpus.jsonl"),
        output_dir=Path("reports/demo_runs") / run_id,
        enable_web_search=False,
        web_search_provider="wikipedia",
        max_web_results=3,
        request_id="req-worker-test",
    )


@pytest.mark.asyncio
async def test_demo_worker_claims_and_finishes_run(tmp_path) -> None:
    store = DemoRunStore(tmp_path / "runs.sqlite3")
    store.create(_run("demo_success"))
    executed: list[str] = []

    async def executor(job: DemoRun) -> None:
        executed.append(job.run_id)

    worker = DemoRunWorker(store, worker_id="worker-one", executor=executor)

    result = await worker.run_once()

    assert result is not None
    assert result.status == "succeeded"
    assert result.worker_id == "worker-one"
    assert result.attempt_count == 1
    assert result.lease_expires_at is None
    assert executed == ["demo_success"]
    assert await worker.run_once() is None


@pytest.mark.asyncio
async def test_demo_worker_persists_executor_failure(tmp_path) -> None:
    store = DemoRunStore(tmp_path / "runs.sqlite3")
    store.create(_run("demo_failure"))

    async def executor(job: DemoRun) -> None:
        raise RuntimeError(f"failed {job.run_id}")

    worker = DemoRunWorker(store, worker_id="worker-two", executor=executor)

    result = await worker.run_once()

    assert result is not None
    assert result.status == "failed"
    assert result.error == "failed demo_failure"
    assert result.worker_id == "worker-two"


def test_demo_worker_validates_lease_configuration(tmp_path) -> None:
    store = DemoRunStore(tmp_path / "runs.sqlite3")

    with pytest.raises(ValueError, match="lease_seconds"):
        DemoRunWorker(store, worker_id="worker", lease_seconds=2)
    with pytest.raises(ValueError, match="worker_id"):
        DemoRunWorker(store, worker_id="")

