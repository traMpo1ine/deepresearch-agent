import sqlite3

from deepresearch_agent.memory import SQLiteMemoryStore
from deepresearch_agent.schemas import Evidence, ResearchTask


def test_sqlite_memory_roundtrip(tmp_path) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3")
    task = ResearchTask(question="test memory")
    evidence = Evidence(
        task_id=task.id,
        source_id="source",
        chunk_id="source#1",
        title="Memory",
        text="SQLite stores evidence for later inspection.",
        url="local://memory",
        quote="SQLite stores evidence",
        score=1.0,
    )

    store.start_run("run_test", "question", "2026-01-01T00:00:00+00:00")
    store.add_task("run_test", task)
    store.add_evidence(evidence, run_id="run_test")

    loaded = store.get_evidence(evidence.id)

    assert loaded is not None
    assert loaded.source_id == "source"
    assert store.search_by_task(task.id)[0].id == evidence.id


def test_sqlite_memory_records_schema_version_and_migrations(tmp_path) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3")

    migrations = store.list_schema_migrations()

    assert store.schema_version() == 2
    assert [migration["version"] for migration in migrations] == [1, 2]
    assert "atomic verification results" in migrations[1]["description"]


def test_sqlite_memory_migrates_legacy_verification_trace_table(tmp_path) -> None:
    path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE verification_traces (
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
                reason TEXT NOT NULL
            )
            """
        )
        conn.execute("PRAGMA user_version = 1")

    store = SQLiteMemoryStore(path)
    with sqlite3.connect(path) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(verification_traces)")}

    assert "atomic_results" in columns
    assert store.schema_version() == 2
    assert [migration["version"] for migration in store.list_schema_migrations()] == [1, 2]


def test_sqlite_memory_database_summary_and_runs(tmp_path) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3")
    store.start_run("run_a", "first question", "2026-01-01T00:00:00+00:00")
    store.finish_run("run_a", "2026-01-01T00:00:01+00:00", "succeeded")

    summary = store.database_summary()
    runs = store.list_runs()

    assert summary["schema_version"] == 2
    assert summary["counts"]["runs"] == 1
    assert runs[0]["id"] == "run_a"
    assert runs[0]["status"] == "succeeded"
