import importlib.util
import sys
from pathlib import Path

from deepresearch_agent.memory import SQLiteMemoryStore


spec = importlib.util.spec_from_file_location(
    "inspect_memory",
    Path("scripts/inspect_memory.py"),
)
inspect_memory = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["inspect_memory"] = inspect_memory
spec.loader.exec_module(inspect_memory)


def test_inspect_memory_payload_includes_schema_and_runs(tmp_path) -> None:
    memory_path = tmp_path / "memory.sqlite3"
    store = SQLiteMemoryStore(memory_path)
    store.start_run("run_memory", "inspect memory", "2026-01-01T00:00:00+00:00")
    store.finish_run("run_memory", "2026-01-01T00:00:01+00:00", "succeeded")

    payload = inspect_memory.inspect_memory(
        str(memory_path),
        include_schema=True,
        include_runs=True,
    )

    assert payload["schema"]["schema_version"] == 2
    assert payload["schema"]["counts"]["runs"] == 1
    assert payload["runs"][0]["id"] == "run_memory"
    assert payload["evidence"] == []


def test_inspect_memory_markdown_names_schema_and_runs() -> None:
    markdown = inspect_memory.payload_to_markdown(
        {
            "memory_path": "memory.sqlite3",
            "schema": {
                "schema_version": 2,
                "counts": {"runs": 1},
                "migrations": [
                    {
                        "version": 2,
                        "description": "Add atomic verification results",
                        "applied_at": "2026-01-01 00:00:00",
                    }
                ],
            },
            "runs": [
                {
                    "id": "run_memory",
                    "status": "succeeded",
                    "started_at": "2026-01-01T00:00:00+00:00",
                    "question": "inspect memory",
                }
            ],
            "evidence": [],
        }
    )

    assert "Schema version: `2`" in markdown
    assert "`run_memory`" in markdown
    assert "No evidence found" in markdown
