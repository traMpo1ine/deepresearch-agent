from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.memory import SQLiteMemoryStore  # noqa: E402


def inspect_memory(memory_path: str, limit: int = 20, include_schema: bool = False, include_runs: bool = False) -> dict:
    store = SQLiteMemoryStore(memory_path)
    payload: dict = {
        "memory_path": memory_path,
        "evidence": [evidence_to_dict(item) for item in store.list_evidence(limit=limit)],
    }
    if include_schema:
        payload["schema"] = store.database_summary()
    if include_runs:
        payload["runs"] = store.list_runs(limit=limit)
    return payload


def evidence_to_dict(item) -> dict:
    return {
        "id": item.id,
        "task_id": item.task_id,
        "source_id": item.source_id,
        "chunk_id": item.chunk_id,
        "title": item.title,
        "url": item.url,
        "quote": item.quote,
        "score": item.score,
    }


def payload_to_markdown(payload: dict) -> str:
    lines = ["# DeepResearch Memory Inspection", "", f"Memory path: `{payload['memory_path']}`", ""]
    schema = payload.get("schema")
    if schema:
        lines.extend(
            [
                "## Schema",
                "",
                f"Schema version: `{schema['schema_version']}`",
                "",
                "### Table Counts",
                "",
            ]
        )
        for table, count in schema["counts"].items():
            lines.append(f"- `{table}`: {count}")
        lines.extend(["", "### Migrations", ""])
        for migration in schema["migrations"]:
            lines.append(
                f"- v{migration['version']}: {migration['description']} "
                f"({migration['applied_at']})"
            )
        lines.append("")
    runs = payload.get("runs")
    if runs is not None:
        lines.extend(["## Runs", ""])
        if not runs:
            lines.append("- No runs found.")
        for run in runs:
            lines.append(
                f"- `{run['id']}` status={run['status']} "
                f"started={run['started_at']} question={run['question']}"
            )
        lines.append("")
    lines.extend(["## Evidence", ""])
    if not payload["evidence"]:
        lines.append("- No evidence found.")
    for item in payload["evidence"]:
        quote = f" | quote={item['quote']}" if item["quote"] else ""
        lines.append(f"- `{item['id']}` | {item['source_id']} | {item['title']}{quote}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect stored DeepResearch memory.")
    parser.add_argument("--memory-path", default="data/memory/deepresearch.sqlite3")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--schema", action="store_true", help="Show schema version, migrations, and table counts.")
    parser.add_argument("--runs", action="store_true", help="Show recent runs.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    args = parser.parse_args()

    payload = inspect_memory(
        memory_path=args.memory_path,
        limit=args.limit,
        include_schema=args.schema,
        include_runs=args.runs,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload_to_markdown(payload))


if __name__ == "__main__":
    main()
