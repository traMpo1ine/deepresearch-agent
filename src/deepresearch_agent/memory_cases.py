from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deepresearch_agent.memory import NumpyVectorIndex, SQLiteMemoryStore
from deepresearch_agent.schemas import Evidence, ResearchTask
from deepresearch_agent.schemas.serialization import to_jsonable


DEFAULT_MEMORY_CASES_PATH = Path("data/examples/memory_cases.jsonl")


@dataclass(slots=True)
class MemoryCase:
    id: str
    question: str
    query: str
    evidence: list[Evidence]
    expected_top_id: str
    learning_note: str


def load_memory_cases(path: str | Path = DEFAULT_MEMORY_CASES_PATH) -> list[MemoryCase]:
    cases: list[MemoryCase] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        cases.append(_case_from_raw(json.loads(line), line_number))
    return cases


def get_memory_case(case_id: str, path: str | Path = DEFAULT_MEMORY_CASES_PATH) -> MemoryCase:
    cases = load_memory_cases(path)
    for case in cases:
        if case.id == case_id:
            return case
    available = ", ".join(case.id for case in cases)
    raise ValueError(f"Unknown memory case '{case_id}'. Available cases: {available}")


def inspect_memory_case(case: MemoryCase) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="deepresearch_memory_case_", ignore_cleanup_errors=True) as tmp:
        tmp_path = Path(tmp)
        store = SQLiteMemoryStore(tmp_path / "memory.sqlite3")
        vector_index = NumpyVectorIndex(dim=64)
        run_id = f"run_{case.id}"
        task = ResearchTask(id=f"task_{case.id}", question=case.question)
        store.start_run(run_id, case.question, "2026-01-01T00:00:00+00:00")
        store.add_task(run_id, task)
        for item in case.evidence:
            store.add_evidence(item, run_id=run_id)
            vector_index.add(item.id, f"{item.title} {item.text} {item.quote or ''}")

        vector_hits = vector_index.search(case.query, top_k=3)
        recalled = [
            {
                "evidence_id": evidence_id,
                "similarity": similarity,
                "record": _evidence_summary(store.get_evidence(evidence_id)),
            }
            for evidence_id, similarity in vector_hits
        ]
        lexical_hits = [_evidence_summary(item) for item in store.search_evidence_text(case.query, limit=3)]
        store.finish_run(run_id, "2026-01-01T00:00:01+00:00")
        return memory_payload(case, run_id, task.id, recalled, lexical_hits)


def memory_payload(
    case: MemoryCase,
    run_id: str,
    task_id: str,
    vector_hits: list[dict[str, Any]],
    lexical_hits: list[dict[str, Any]],
) -> dict[str, Any]:
    observed_top_id = vector_hits[0]["evidence_id"] if vector_hits else None
    return {
        "case_id": case.id,
        "question": case.question,
        "query": case.query,
        "learning_note": case.learning_note,
        "run_id": run_id,
        "task_id": task_id,
        "sqlite_record_count": len(case.evidence),
        "vector_index_count": len(case.evidence),
        "expected_top_id": case.expected_top_id,
        "observed_top_id": observed_top_id,
        "top_match_ok": observed_top_id == case.expected_top_id,
        "vector_hits": vector_hits,
        "lexical_hits": lexical_hits,
    }


def memory_payload_to_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Memory Trace",
        "",
        f"Case: `{payload['case_id']}`",
        "",
        f"Question: {payload['question']}",
        f"Recall query: `{payload['query']}`",
        f"Run id: `{payload['run_id']}`",
        f"Task id: `{payload['task_id']}`",
        f"SQLite records: `{payload['sqlite_record_count']}`",
        f"Vector index items: `{payload['vector_index_count']}`",
        f"Expected top id: `{payload['expected_top_id']}`",
        f"Observed top id: `{payload['observed_top_id']}`",
        f"Top match ok: `{str(payload['top_match_ok']).lower()}`",
        "",
        "## Learning Note",
        "",
        payload["learning_note"],
        "",
        "## Vector Hits",
        "",
    ]
    for index, hit in enumerate(payload["vector_hits"], start=1):
        record = hit["record"]
        lines.extend(
            [
                f"### Hit {index}",
                "",
                f"Evidence id: `{hit['evidence_id']}`",
                f"Similarity: `{hit['similarity']:.3f}`",
                f"Title: {record['title']}",
                f"Quote: {record['quote']}",
                "",
            ]
        )
    lines.extend(["## Lexical Hits", ""])
    for hit in payload["lexical_hits"]:
        lines.append(f"- `{hit['id']}` {hit['title']} | quote={hit['quote']}")
    return "\n".join(lines)


def list_memory_cases_markdown(cases: list[MemoryCase]) -> str:
    lines = ["# Memory Cases", ""]
    for case in cases:
        lines.append(f"- `{case.id}`: expected top `{case.expected_top_id}` - {case.learning_note}")
    return "\n".join(lines)


def payload_json(payload: dict[str, Any]) -> str:
    return json.dumps(to_jsonable(payload), ensure_ascii=False, indent=2)


def _case_from_raw(raw: dict[str, Any], line_number: int) -> MemoryCase:
    required = {"id", "question", "query", "evidence", "expected_top_id", "learning_note"}
    missing = sorted(required - set(raw))
    if missing:
        raise ValueError(f"Memory case line {line_number} is missing fields: {missing}")
    return MemoryCase(
        id=str(raw["id"]),
        question=str(raw["question"]),
        query=str(raw["query"]),
        evidence=[Evidence(**item) for item in raw["evidence"]],
        expected_top_id=str(raw["expected_top_id"]),
        learning_note=str(raw["learning_note"]),
    )


def _evidence_summary(evidence: Evidence | None) -> dict[str, Any]:
    if evidence is None:
        return {"id": None, "title": None, "source_id": None, "chunk_id": None, "quote": None}
    return {
        "id": evidence.id,
        "title": evidence.title,
        "source_id": evidence.source_id,
        "chunk_id": evidence.chunk_id,
        "quote": evidence.quote,
        "score": evidence.score,
    }
