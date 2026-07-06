from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from deepresearch_agent.schemas import Claim, Evidence, RepairAction, ResearchReport, ResearchTask, VerificationTrace
from deepresearch_agent.schemas.serialization import to_jsonable


SCHEMA_VERSION = 2
MIGRATIONS = {
    1: "Initial persistent memory schema with verification traces",
    2: "Add atomic verification results to verification_traces",
}

SUMMARY_TABLES = (
    "runs",
    "tasks",
    "evidence",
    "claims",
    "reports",
    "agent_events",
    "verification_traces",
    "repair_actions",
)


class SQLiteMemoryStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    description TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    status TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    dependencies TEXT NOT NULL,
                    retry_count INTEGER NOT NULL,
                    error TEXT,
                    metadata TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY,
                    run_id TEXT,
                    task_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    chunk_id TEXT,
                    title TEXT NOT NULL,
                    text TEXT NOT NULL,
                    url TEXT NOT NULL,
                    quote TEXT,
                    quote_start INTEGER,
                    quote_end INTEGER,
                    score REAL NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS claims (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    citation_ids TEXT NOT NULL,
                    verification_status TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reports (
                    run_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    markdown TEXT NOT NULL,
                    json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    ok INTEGER NOT NULL,
                    latency_seconds REAL NOT NULL,
                    error TEXT,
                    metadata TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS verification_traces (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    claim_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    matched_evidence_ids TEXT NOT NULL,
                    support_terms TEXT NOT NULL,
                    missing_terms TEXT NOT NULL,
                    citation_presence INTEGER NOT NULL,
                    term_overlap REAL NOT NULL,
                    quote_overlap REAL NOT NULL,
                    contradiction_cues TEXT NOT NULL,
                    support_level TEXT NOT NULL,
                    atomic_claims TEXT NOT NULL,
                    atomic_results TEXT NOT NULL DEFAULT '[]',
                    reason TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS repair_actions (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    target_claim_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    patch TEXT NOT NULL,
                    before_text TEXT,
                    after_text TEXT
                )
                """
            )
            self._ensure_column(conn, "verification_traces", "atomic_results", "TEXT NOT NULL DEFAULT '[]'")
            self._record_migration(conn, 1)
            self._record_migration(conn, 2)
            conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def _ensure_column(
        self,
        conn: sqlite3.Connection,
        table: str,
        column: str,
        definition: str,
    ) -> None:
        columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in columns:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def _record_migration(self, conn: sqlite3.Connection, version: int) -> None:
        conn.execute(
            """
            INSERT OR IGNORE INTO schema_migrations (version, description)
            VALUES (?, ?)
            """,
            (version, MIGRATIONS[version]),
        )

    def schema_version(self) -> int:
        with self._connect() as conn:
            row = conn.execute("PRAGMA user_version").fetchone()
        return int(row[0]) if row else 0

    def list_schema_migrations(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT version, applied_at, description FROM schema_migrations ORDER BY version"
            ).fetchall()
        return [
            {
                "version": row["version"],
                "applied_at": row["applied_at"],
                "description": row["description"],
            }
            for row in rows
        ]

    def start_run(self, run_id: str, question: str, started_at: str, metadata: dict | None = None) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO runs
                (id, question, started_at, finished_at, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (run_id, question, started_at, None, "running", self._json(metadata or {})),
            )

    def finish_run(self, run_id: str, finished_at: str, status: str = "succeeded") -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE runs SET finished_at = ?, status = ? WHERE id = ?",
                (finished_at, status, run_id),
            )

    def get_run(self, run_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "question": row["question"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "status": row["status"],
            "metadata": json.loads(row["metadata"]),
        }

    def list_runs(self, limit: int = 20) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM runs ORDER BY started_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "question": row["question"],
                "started_at": row["started_at"],
                "finished_at": row["finished_at"],
                "status": row["status"],
                "metadata": json.loads(row["metadata"]),
            }
            for row in rows
        ]

    def database_summary(self) -> dict:
        with self._connect() as conn:
            counts = {
                table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in SUMMARY_TABLES
            }
        return {
            "path": str(self.path),
            "schema_version": self.schema_version(),
            "migrations": self.list_schema_migrations(),
            "counts": counts,
        }

    def add_task(self, run_id: str, task: ResearchTask) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO tasks
                (id, run_id, question, task_type, status, dependencies, retry_count, error, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.id,
                    run_id,
                    task.question,
                    task.task_type.value,
                    task.status.value,
                    self._json(task.dependencies),
                    task.retry_count,
                    task.error,
                    self._json({"priority": task.priority, "expected_evidence": task.expected_evidence}),
                ),
            )

    def add_evidence(self, evidence: Evidence, run_id: str | None = None) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO evidence
                (id, run_id, task_id, source_id, chunk_id, title, text, url, quote,
                 quote_start, quote_end, score, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence.id,
                    run_id,
                    evidence.task_id,
                    evidence.source_id,
                    evidence.chunk_id,
                    evidence.title,
                    evidence.text,
                    evidence.url,
                    evidence.quote,
                    evidence.quote_start,
                    evidence.quote_end,
                    evidence.score,
                    self._json(evidence.metadata),
                ),
            )

    def add_claim(self, run_id: str, claim: Claim) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO claims
                (id, run_id, text, citation_ids, verification_status, confidence, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    claim.id,
                    run_id,
                    claim.text,
                    self._json(claim.citation_ids),
                    claim.verification_status.value,
                    claim.confidence,
                    self._json(
                        {
                            "reason": claim.verification_reason,
                            "matched_evidence_ids": claim.matched_evidence_ids,
                            "missing_terms": claim.missing_terms,
                        }
                    ),
                ),
            )
        if claim.verification_trace:
            self.add_verification_trace(run_id, claim.verification_trace)

    def add_verification_trace(self, run_id: str, trace: VerificationTrace) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO verification_traces
                (id, run_id, claim_id, status, matched_evidence_ids, support_terms,
                 missing_terms, citation_presence, term_overlap, quote_overlap,
                 contradiction_cues, support_level, atomic_claims, atomic_results, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace.id,
                    run_id,
                    trace.claim_id,
                    trace.status.value,
                    self._json(trace.matched_evidence_ids),
                    self._json(trace.support_terms),
                    self._json(trace.missing_terms),
                    int(trace.citation_presence),
                    trace.term_overlap,
                    trace.quote_overlap,
                    self._json(trace.contradiction_cues),
                    trace.support_level,
                    self._json(trace.atomic_claims),
                    self._json(to_jsonable(trace.atomic_results)),
                    trace.reason,
                ),
            )

    def add_repair_action(self, run_id: str, action: RepairAction) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO repair_actions
                (id, run_id, action_type, target_claim_id, reason, patch, before_text, after_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    action.id,
                    run_id,
                    action.action_type.value,
                    action.target_claim_id,
                    action.reason,
                    action.patch,
                    action.before,
                    action.after,
                ),
            )

    def add_report(self, report: ResearchReport) -> None:
        if report.run_id is None:
            raise ValueError("report.run_id is required")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO reports (run_id, title, markdown, json)
                VALUES (?, ?, ?, ?)
                """,
                (report.run_id, report.title, report.to_markdown(), report.to_json()),
            )

    def update_run_metadata(self, run_id: str, metadata: dict) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE runs SET metadata = ? WHERE id = ?", (self._json(metadata), run_id))

    def add_agent_event(
        self,
        run_id: str,
        agent_name: str,
        ok: bool,
        latency_seconds: float,
        error: str | None,
        metadata: dict | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_events
                (run_id, agent_name, ok, latency_seconds, error, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (run_id, agent_name, int(ok), latency_seconds, error, self._json(metadata or {})),
            )

    def get_evidence(self, evidence_id: str) -> Evidence | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM evidence WHERE id = ?", (evidence_id,)).fetchone()
        return self._row_to_evidence(row) if row else None

    def list_evidence(self, limit: int = 100) -> list[Evidence]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM evidence ORDER BY rowid DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._row_to_evidence(row) for row in rows]

    def search_by_task(self, task_id: str) -> list[Evidence]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM evidence WHERE task_id = ?", (task_id,)).fetchall()
        return [self._row_to_evidence(row) for row in rows]

    def list_tasks(self, run_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM tasks WHERE run_id = ?", (run_id,)).fetchall()
        return [
            {
                "id": row["id"],
                "question": row["question"],
                "task_type": row["task_type"],
                "status": row["status"],
                "dependencies": json.loads(row["dependencies"]),
                "retry_count": row["retry_count"],
                "error": row["error"],
                "metadata": json.loads(row["metadata"]),
            }
            for row in rows
        ]

    def list_agent_events(self, run_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM agent_events WHERE run_id = ?", (run_id,)).fetchall()
        return [
            {
                "agent_name": row["agent_name"],
                "ok": bool(row["ok"]),
                "latency_seconds": row["latency_seconds"],
                "error": row["error"],
                "metadata": json.loads(row["metadata"]),
            }
            for row in rows
        ]

    def search_evidence_text(self, query: str, limit: int = 10) -> list[Evidence]:
        terms = [term for term in query.lower().split() if len(term) > 3]
        if not terms:
            return []
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM evidence").fetchall()
        ranked = []
        for row in rows:
            text = f"{row['title']} {row['text']} {row['quote'] or ''}".lower()
            score = sum(1 for term in terms if term in text)
            if score:
                ranked.append((score, row))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [self._row_to_evidence(row) for _, row in ranked[:limit]]

    def _row_to_evidence(self, row: sqlite3.Row) -> Evidence:
        return Evidence(
            id=row["id"],
            task_id=row["task_id"],
            source_id=row["source_id"],
            chunk_id=row["chunk_id"],
            title=row["title"],
            text=row["text"],
            url=row["url"],
            quote=row["quote"],
            quote_start=row["quote_start"],
            quote_end=row["quote_end"],
            score=row["score"],
            metadata=json.loads(row["metadata"]),
        )

    def _json(self, value: object) -> str:
        return json.dumps(value, ensure_ascii=False)
