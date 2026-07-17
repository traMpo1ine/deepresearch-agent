from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
import sqlite3

import pytest

from deepresearch_agent.web.run_store import (
    DemoRun,
    DemoRunStore,
    IdempotencyConflictError,
    RunCapacityError,
)


def _run(run_id: str = "demo_test", updated_at: str | None = None) -> DemoRun:
    timestamp = updated_at or datetime.now(UTC).isoformat()
    return DemoRun(
        run_id=run_id,
        question="Why persist Agent task state?",
        backend="mock",
        model=None,
        repair_rounds=2,
        corpus_profile="offline_agent_docs",
        corpus_path=Path("data/corpus/offline_corpus.jsonl"),
        output_dir=Path("reports/demo_runs") / run_id,
        enable_web_search=True,
        web_search_provider="wikipedia,arxiv",
        max_web_results=4,
        request_id="req-test",
        created_at=timestamp,
        updated_at=timestamp,
    )


def test_demo_run_store_survives_reopen_and_records_schema_version(tmp_path: Path) -> None:
    path = tmp_path / "runs.sqlite3"
    store = DemoRunStore(path)
    store.create(_run())

    reopened = DemoRunStore(path)
    actual = reopened.get("demo_test")

    assert actual is not None
    assert actual.question == "Why persist Agent task state?"
    assert actual.enable_web_search is True
    assert reopened.is_ready() is True
    with reopened._connect() as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 4


def test_demo_run_store_claim_is_atomic_across_workers(tmp_path: Path) -> None:
    store = DemoRunStore(tmp_path / "runs.sqlite3")
    store.create(_run("demo_atomic"))

    with ThreadPoolExecutor(max_workers=4) as pool:
        claimed = list(pool.map(lambda _: store.claim("demo_atomic"), range(4)))

    winners = [run for run in claimed if run is not None]
    assert len(winners) == 1
    assert winners[0].status == "running"
    finished = store.finish("demo_atomic", "succeeded")
    assert finished.status == "succeeded"
    assert store.status_counts() == {"succeeded": 1}
    assert [run.run_id for run in store.list_recent(status="succeeded")] == ["demo_atomic"]


def test_demo_run_store_recovers_stale_incomplete_runs(tmp_path: Path) -> None:
    old = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    store = DemoRunStore(tmp_path / "runs.sqlite3")
    store.create(_run("demo_stale", updated_at=old))

    recovered = store.recover_stale(stale_after_seconds=3600)
    actual = store.get("demo_stale")

    assert recovered == 1
    assert actual is not None
    assert actual.status == "failed"
    assert actual.error == "worker_interrupted_or_lease_expired"


def test_demo_run_store_rejects_invalid_transitions(tmp_path: Path) -> None:
    store = DemoRunStore(tmp_path / "runs.sqlite3")
    invalid = _run("demo_invalid")
    invalid.status = "mystery"

    with pytest.raises(ValueError, match="Unsupported"):
        store.create(invalid)

    store.create(_run("demo_not_running"))
    with pytest.raises(RuntimeError, match="not in running state"):
        store.finish("demo_not_running", "failed")
    with pytest.raises(ValueError, match="must be succeeded or failed"):
        store.finish("demo_not_running", "running")


def test_demo_run_store_idempotency_replays_before_capacity_check(tmp_path: Path) -> None:
    store = DemoRunStore(tmp_path / "runs.sqlite3")
    original = _run("demo_original")
    original.idempotency_key = "client-operation-1"
    original.request_fingerprint = "a" * 64

    admitted, created = store.admit(original, max_active_runs=1)
    duplicate = _run("demo_duplicate")
    duplicate.idempotency_key = "client-operation-1"
    duplicate.request_fingerprint = "a" * 64
    replayed, replay_created = store.admit(duplicate, max_active_runs=1)

    assert created is True
    assert admitted.run_id == "demo_original"
    assert replay_created is False
    assert replayed.run_id == "demo_original"


def test_demo_run_store_rejects_idempotency_key_payload_conflict(tmp_path: Path) -> None:
    store = DemoRunStore(tmp_path / "runs.sqlite3")
    original = _run("demo_original")
    original.idempotency_key = "client-operation-1"
    original.request_fingerprint = "a" * 64
    store.admit(original, max_active_runs=2)
    conflicting = _run("demo_conflict")
    conflicting.idempotency_key = "client-operation-1"
    conflicting.request_fingerprint = "b" * 64

    with pytest.raises(IdempotencyConflictError, match="different request payload"):
        store.admit(conflicting, max_active_runs=2)


def test_demo_run_store_capacity_admission_is_atomic(tmp_path: Path) -> None:
    store = DemoRunStore(tmp_path / "runs.sqlite3")

    def admit(index: int):
        try:
            return store.admit(_run(f"demo_capacity_{index}"), max_active_runs=1)
        except RunCapacityError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(admit, range(2)))

    assert sum(outcome is not None for outcome in outcomes) == 1
    assert store.status_counts() == {"queued": 1}


def test_demo_run_store_migrates_v1_database_to_v4(tmp_path: Path) -> None:
    path = tmp_path / "runs_v1.sqlite3"
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE demo_runs (
                run_id TEXT PRIMARY KEY, question TEXT NOT NULL, backend TEXT NOT NULL,
                model TEXT, repair_rounds INTEGER NOT NULL, corpus_profile TEXT NOT NULL,
                corpus_path TEXT NOT NULL, output_dir TEXT NOT NULL,
                enable_web_search INTEGER NOT NULL, web_search_provider TEXT NOT NULL,
                max_web_results INTEGER NOT NULL, request_id TEXT NOT NULL,
                status TEXT NOT NULL, error TEXT, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            PRAGMA user_version = 1;
            """
        )

    store = DemoRunStore(path)

    with store._connect() as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(demo_runs)")}
        indexes = {row[1] for row in conn.execute("PRAGMA index_list(demo_runs)")}
        version = conn.execute("PRAGMA user_version").fetchone()[0]
    assert "idempotency_key" in columns
    assert "request_fingerprint" in columns
    assert {"worker_id", "lease_expires_at", "attempt_count"} <= columns
    assert "idx_demo_runs_idempotency_key" in indexes
    assert version == 4


def test_demo_run_store_claim_next_is_atomic_and_fifo(tmp_path: Path) -> None:
    store = DemoRunStore(tmp_path / "runs.sqlite3")
    first = _run("demo_first")
    second = _run("demo_second")
    second.created_at = (datetime.now(UTC) + timedelta(seconds=1)).isoformat()
    second.updated_at = second.created_at
    store.create(first)
    store.create(second)

    with ThreadPoolExecutor(max_workers=4) as pool:
        claimed = list(
            pool.map(lambda index: store.claim_next(f"worker-{index}"), range(4))
        )

    winners = [run for run in claimed if run is not None]
    assert {run.run_id for run in winners} == {"demo_first", "demo_second"}
    assert all(run.worker_id for run in winners)
    assert all(run.attempt_count == 1 for run in winners)


def test_demo_run_store_heartbeat_checks_worker_ownership(tmp_path: Path) -> None:
    store = DemoRunStore(tmp_path / "runs.sqlite3")
    store.create(_run("demo_heartbeat"))
    claimed = store.claim_next("worker-owner", lease_seconds=30)

    assert claimed is not None
    original_lease = claimed.lease_expires_at
    assert store.heartbeat("demo_heartbeat", "other-worker", lease_seconds=60) is False
    assert store.heartbeat("demo_heartbeat", "worker-owner", lease_seconds=60) is True
    refreshed = store.get("demo_heartbeat")
    assert refreshed is not None
    assert refreshed.lease_expires_at != original_lease


def test_demo_run_store_requeues_then_fails_expired_lease(tmp_path: Path) -> None:
    store = DemoRunStore(tmp_path / "runs.sqlite3")
    store.create(_run("demo_lease"))
    assert store.claim_next("worker-one", lease_seconds=30) is not None
    expired = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
    with store._connect() as conn:
        conn.execute(
            "UPDATE demo_runs SET lease_expires_at = ? WHERE run_id = ?",
            (expired, "demo_lease"),
        )

    assert store.recover_expired_leases(max_attempts=2) == {"requeued": 1, "failed": 0}
    requeued = store.get("demo_lease")
    assert requeued is not None
    assert requeued.status == "queued"
    assert store.claim_next("worker-two", lease_seconds=30) is not None
    with store._connect() as conn:
        conn.execute(
            "UPDATE demo_runs SET lease_expires_at = ? WHERE run_id = ?",
            (expired, "demo_lease"),
        )

    assert store.recover_expired_leases(max_attempts=2) == {"requeued": 0, "failed": 1}
    failed = store.get("demo_lease")
    assert failed is not None
    assert failed.status == "failed"
    assert failed.error == "worker_lease_expired_max_attempts"
