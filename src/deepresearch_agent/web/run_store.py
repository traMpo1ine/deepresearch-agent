from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path


RUN_STATUSES = {"queued", "running", "succeeded", "failed"}


class RunCapacityError(RuntimeError):
    """Raised when active queued/running jobs reach the configured capacity."""


class IdempotencyConflictError(RuntimeError):
    """Raised when an idempotency key is reused with a different request payload."""


@dataclass(slots=True)
class DemoRun:
    run_id: str
    question: str
    backend: str
    model: str | None
    repair_rounds: int
    corpus_profile: str
    corpus_path: Path
    output_dir: Path
    enable_web_search: bool
    web_search_provider: str
    max_web_results: int
    request_id: str
    idempotency_key: str | None = None
    request_fingerprint: str | None = None
    worker_id: str | None = None
    lease_expires_at: str | None = None
    attempt_count: int = 0
    status: str = "queued"
    error: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class DemoRunStore:
    """WAL SQLite registry with transactional run-state transitions."""

    schema_version = 4

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._migrate()

    def create(self, run: DemoRun) -> None:
        self._validate_status(run.status)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO demo_runs (
                    run_id, question, backend, model, repair_rounds, corpus_profile,
                    corpus_path, output_dir, enable_web_search, web_search_provider,
                    max_web_results, request_id, idempotency_key, request_fingerprint,
                    worker_id, lease_expires_at, attempt_count,
                    status, error, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._values(run),
            )

    def admit(self, run: DemoRun, max_active_runs: int) -> tuple[DemoRun, bool]:
        """Atomically replay an idempotent request or admit it under active capacity."""
        capacity = max(1, max_active_runs)
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            if run.idempotency_key:
                existing = conn.execute(
                    "SELECT * FROM demo_runs WHERE idempotency_key = ?",
                    (run.idempotency_key,),
                ).fetchone()
                if existing is not None:
                    existing_fingerprint = existing["request_fingerprint"]
                    if (
                        existing_fingerprint is not None
                        and run.request_fingerprint is not None
                        and existing_fingerprint != run.request_fingerprint
                    ):
                        conn.rollback()
                        raise IdempotencyConflictError(
                            "Idempotency-Key was already used with a different request payload."
                        )
                    conn.commit()
                    return self._from_row(existing), False
            active_count = int(
                conn.execute(
                    "SELECT COUNT(*) FROM demo_runs WHERE status IN ('queued', 'running')"
                ).fetchone()[0]
            )
            if active_count >= capacity:
                conn.rollback()
                raise RunCapacityError(
                    f"Active demo run capacity reached ({active_count}/{capacity})."
                )
            conn.execute(
                """
                INSERT INTO demo_runs (
                    run_id, question, backend, model, repair_rounds, corpus_profile,
                    corpus_path, output_dir, enable_web_search, web_search_provider,
                    max_web_results, request_id, idempotency_key, request_fingerprint,
                    worker_id, lease_expires_at, attempt_count,
                    status, error, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._values(run),
            )
            conn.commit()
            return run, True
        except Exception:
            if conn.in_transaction:
                conn.rollback()
            raise
        finally:
            conn.close()

    def get(self, run_id: str) -> DemoRun | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM demo_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        return self._from_row(row) if row else None

    def claim(
        self,
        run_id: str,
        worker_id: str = "background",
        lease_seconds: int = 3600,
    ) -> DemoRun | None:
        """Atomically allow exactly one worker to move queued -> running."""
        now = datetime.now(UTC)
        updated_at = now.isoformat()
        lease_expires_at = (now + timedelta(seconds=max(1, lease_seconds))).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE demo_runs
                SET status = 'running', error = NULL, updated_at = ?, worker_id = ?,
                    lease_expires_at = ?, attempt_count = attempt_count + 1
                WHERE run_id = ? AND status = 'queued'
                """,
                (updated_at, worker_id, lease_expires_at, run_id),
            )
            if cursor.rowcount != 1:
                return None
        return self.get(run_id)

    def claim_next(self, worker_id: str, lease_seconds: int = 120) -> DemoRun | None:
        """FIFO claim for a standalone worker, serialized by BEGIN IMMEDIATE."""
        now = datetime.now(UTC)
        updated_at = now.isoformat()
        lease_expires_at = (now + timedelta(seconds=max(1, lease_seconds))).isoformat()
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """
                SELECT run_id FROM demo_runs
                WHERE status = 'queued'
                ORDER BY created_at ASC, run_id ASC
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                conn.commit()
                return None
            run_id = str(row["run_id"])
            cursor = conn.execute(
                """
                UPDATE demo_runs
                SET status = 'running', error = NULL, updated_at = ?, worker_id = ?,
                    lease_expires_at = ?, attempt_count = attempt_count + 1
                WHERE run_id = ? AND status = 'queued'
                """,
                (updated_at, worker_id, lease_expires_at, run_id),
            )
            if cursor.rowcount != 1:  # pragma: no cover - guarded by write lock.
                conn.rollback()
                return None
            conn.commit()
        finally:
            conn.close()
        return self.get(run_id)

    def heartbeat(self, run_id: str, worker_id: str, lease_seconds: int = 120) -> bool:
        now = datetime.now(UTC)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE demo_runs
                SET updated_at = ?, lease_expires_at = ?
                WHERE run_id = ? AND status = 'running' AND worker_id = ?
                """,
                (
                    now.isoformat(),
                    (now + timedelta(seconds=max(1, lease_seconds))).isoformat(),
                    run_id,
                    worker_id,
                ),
            )
            return cursor.rowcount == 1

    def finish(
        self,
        run_id: str,
        status: str,
        error: str | None = None,
        worker_id: str | None = None,
    ) -> DemoRun:
        if status not in {"succeeded", "failed"}:
            raise ValueError("A finished demo run must be succeeded or failed.")
        updated_at = datetime.now(UTC).isoformat()
        ownership_sql = " AND worker_id = ?" if worker_id is not None else ""
        parameters: tuple[object, ...] = (status, error, updated_at, run_id)
        if worker_id is not None:
            parameters = (*parameters, worker_id)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE demo_runs
                SET status = ?, error = ?, updated_at = ?, lease_expires_at = NULL
                WHERE run_id = ? AND status = 'running'
                """
                + ownership_sql,
                parameters,
            )
            if cursor.rowcount != 1:
                raise RuntimeError(f"Demo run {run_id} is not in running state.")
        run = self.get(run_id)
        if run is None:  # pragma: no cover - protected by the transaction above.
            raise RuntimeError(f"Demo run disappeared after update: {run_id}")
        return run

    def recover_expired_leases(self, max_attempts: int = 3) -> dict[str, int]:
        """Requeue interrupted work, then fail it after a bounded number of attempts."""
        now = datetime.now(UTC).isoformat()
        attempts = max(1, max_attempts)
        with self._connect() as conn:
            failed = conn.execute(
                """
                UPDATE demo_runs
                SET status = 'failed', error = 'worker_lease_expired_max_attempts',
                    worker_id = NULL, lease_expires_at = NULL, updated_at = ?
                WHERE status = 'running' AND lease_expires_at IS NOT NULL
                    AND lease_expires_at < ? AND attempt_count >= ?
                """,
                (now, now, attempts),
            ).rowcount
            requeued = conn.execute(
                """
                UPDATE demo_runs
                SET status = 'queued', error = 'worker_lease_expired_requeued',
                    worker_id = NULL, lease_expires_at = NULL, updated_at = ?
                WHERE status = 'running' AND lease_expires_at IS NOT NULL
                    AND lease_expires_at < ? AND attempt_count < ?
                """,
                (now, now, attempts),
            ).rowcount
        return {"requeued": requeued, "failed": failed}

    def recover_stale(self, stale_after_seconds: int = 3600) -> int:
        threshold = (
            datetime.now(UTC) - timedelta(seconds=max(1, stale_after_seconds))
        ).isoformat()
        now = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE demo_runs
                SET status = 'failed', error = 'worker_interrupted_or_lease_expired', updated_at = ?
                WHERE status IN ('queued', 'running') AND updated_at < ?
                """,
                (now, threshold),
            )
            return cursor.rowcount

    def status_counts(self) -> dict[str, int]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) AS count FROM demo_runs GROUP BY status"
            ).fetchall()
        return {str(row["status"]): int(row["count"]) for row in rows}

    def list_recent(self, limit: int = 20, status: str | None = None) -> list[DemoRun]:
        safe_limit = min(max(1, limit), 100)
        if status is not None:
            self._validate_status(status)
        with self._connect() as conn:
            if status is None:
                rows = conn.execute(
                    "SELECT * FROM demo_runs ORDER BY updated_at DESC LIMIT ?",
                    (safe_limit,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM demo_runs WHERE status = ? "
                    "ORDER BY updated_at DESC LIMIT ?",
                    (status, safe_limit),
                ).fetchall()
        return [self._from_row(row) for row in rows]

    def is_ready(self) -> bool:
        try:
            with self._connect() as conn:
                row = conn.execute("SELECT 1 FROM demo_runs LIMIT 1").fetchone()
            return row is None or int(row[0]) == 1
        except sqlite3.Error:
            return False

    def _migrate(self) -> None:
        with self._connect() as conn:
            version = int(conn.execute("PRAGMA user_version").fetchone()[0])
            if version > self.schema_version:
                raise RuntimeError(
                    f"DemoRunStore schema {version} is newer than supported {self.schema_version}."
                )
            if version == 0:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS demo_runs (
                        run_id TEXT PRIMARY KEY,
                        question TEXT NOT NULL,
                        backend TEXT NOT NULL,
                        model TEXT,
                        repair_rounds INTEGER NOT NULL,
                        corpus_profile TEXT NOT NULL,
                        corpus_path TEXT NOT NULL,
                        output_dir TEXT NOT NULL,
                        enable_web_search INTEGER NOT NULL,
                        web_search_provider TEXT NOT NULL,
                        max_web_results INTEGER NOT NULL,
                        request_id TEXT NOT NULL,
                        idempotency_key TEXT,
                        request_fingerprint TEXT,
                        worker_id TEXT,
                        lease_expires_at TEXT,
                        attempt_count INTEGER NOT NULL DEFAULT 0,
                        status TEXT NOT NULL CHECK (
                            status IN ('queued', 'running', 'succeeded', 'failed')
                        ),
                        error TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_demo_runs_status_updated "
                    "ON demo_runs(status, updated_at)"
                )
                conn.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_demo_runs_idempotency_key "
                    "ON demo_runs(idempotency_key) WHERE idempotency_key IS NOT NULL"
                )
                conn.execute(f"PRAGMA user_version = {self.schema_version}")
                return
            elif version == 1:
                conn.execute("ALTER TABLE demo_runs ADD COLUMN idempotency_key TEXT")
                conn.execute(
                    "CREATE UNIQUE INDEX idx_demo_runs_idempotency_key "
                    "ON demo_runs(idempotency_key) WHERE idempotency_key IS NOT NULL"
                )
                conn.execute("ALTER TABLE demo_runs ADD COLUMN request_fingerprint TEXT")
                version = 3
            elif version == 2:
                conn.execute("ALTER TABLE demo_runs ADD COLUMN request_fingerprint TEXT")
                version = 3
            if version == 3:
                conn.execute("ALTER TABLE demo_runs ADD COLUMN worker_id TEXT")
                conn.execute("ALTER TABLE demo_runs ADD COLUMN lease_expires_at TEXT")
                conn.execute(
                    "ALTER TABLE demo_runs ADD COLUMN attempt_count INTEGER NOT NULL DEFAULT 0"
                )
                conn.execute("PRAGMA user_version = 4")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=10000")
        return conn

    @staticmethod
    def _validate_status(status: str) -> None:
        if status not in RUN_STATUSES:
            raise ValueError(f"Unsupported demo run status: {status}")

    @staticmethod
    def _values(run: DemoRun) -> tuple[object, ...]:
        return (
            run.run_id,
            run.question,
            run.backend,
            run.model,
            run.repair_rounds,
            run.corpus_profile,
            str(run.corpus_path),
            str(run.output_dir),
            int(run.enable_web_search),
            run.web_search_provider,
            run.max_web_results,
            run.request_id,
            run.idempotency_key,
            run.request_fingerprint,
            run.worker_id,
            run.lease_expires_at,
            run.attempt_count,
            run.status,
            run.error,
            run.created_at,
            run.updated_at,
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> DemoRun:
        return DemoRun(
            run_id=str(row["run_id"]),
            question=str(row["question"]),
            backend=str(row["backend"]),
            model=str(row["model"]) if row["model"] is not None else None,
            repair_rounds=int(row["repair_rounds"]),
            corpus_profile=str(row["corpus_profile"]),
            corpus_path=Path(str(row["corpus_path"])),
            output_dir=Path(str(row["output_dir"])),
            enable_web_search=bool(row["enable_web_search"]),
            web_search_provider=str(row["web_search_provider"]),
            max_web_results=int(row["max_web_results"]),
            request_id=str(row["request_id"]),
            idempotency_key=(
                str(row["idempotency_key"]) if row["idempotency_key"] is not None else None
            ),
            request_fingerprint=(
                str(row["request_fingerprint"])
                if row["request_fingerprint"] is not None
                else None
            ),
            worker_id=str(row["worker_id"]) if row["worker_id"] is not None else None,
            lease_expires_at=(
                str(row["lease_expires_at"])
                if row["lease_expires_at"] is not None
                else None
            ),
            attempt_count=int(row["attempt_count"]),
            status=str(row["status"]),
            error=str(row["error"]) if row["error"] is not None else None,
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )
