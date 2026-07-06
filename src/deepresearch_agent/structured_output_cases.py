from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deepresearch_agent.structured_output import StructuredOutputParser


DEFAULT_STRUCTURED_OUTPUT_CASES_PATH = Path("data/examples/structured_output_cases.jsonl")
DEFAULT_SCHEMA = {"title": "Untitled", "claims": [], "citations": []}


@dataclass(slots=True)
class StructuredOutputCase:
    id: str
    text: str
    expected_ok: bool
    expected_level: int


def load_structured_output_cases(
    path: str | Path = DEFAULT_STRUCTURED_OUTPUT_CASES_PATH,
) -> list[StructuredOutputCase]:
    cases: list[StructuredOutputCase] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        cases.append(
            StructuredOutputCase(
                id=str(raw["id"]),
                text=str(raw["text"]),
                expected_ok=bool(raw["expected_ok"]),
                expected_level=int(raw["expected_level"]),
            )
        )
    return cases


def inspect_structured_output_case(case_id: str) -> dict[str, Any]:
    for case in load_structured_output_cases():
        if case.id == case_id:
            result = StructuredOutputParser().parse(case.text, DEFAULT_SCHEMA)
            return {
                "case_id": case.id,
                "expected_ok": case.expected_ok,
                "actual_ok": result.ok,
                "expected_level": case.expected_level,
                "actual_level": result.parse_level,
                "data": result.data,
                "metadata": result.metadata(),
            }
    available = ", ".join(case.id for case in load_structured_output_cases())
    raise ValueError(f"Unknown structured output case '{case_id}'. Available cases: {available}")


def structured_output_summary() -> dict[str, Any]:
    cases = load_structured_output_cases()
    parser = StructuredOutputParser()
    parsed = [parser.parse(case.text, DEFAULT_SCHEMA) for case in cases]
    ok_count = sum(1 for result in parsed if result.ok)
    strict_count = sum(1 for result in parsed if result.ok and result.parse_level == 1)
    fallback_count = sum(1 for result in parsed if result.ok and result.parse_level in {2, 3})
    warning_count = sum(len(result.warnings) for result in parsed)
    schema_repair_warning_count = sum(
        1
        for result in parsed
        for warning in result.warnings
        if "schema" in warning.lower() or "missing" in warning.lower()
    )
    by_level: dict[str, int] = {}
    for result in parsed:
        by_level[str(result.parse_level)] = by_level.get(str(result.parse_level), 0) + 1
    return {
        "case_count": len(cases),
        "strict_parse_success_count": strict_count,
        "strict_parse_success_rate": strict_count / len(cases) if cases else 0.0,
        "fallback_parse_success_count": fallback_count,
        "fallback_parse_success_rate": fallback_count / len(cases) if cases else 0.0,
        "parse_success_count": ok_count,
        "parse_success_rate": ok_count / len(cases) if cases else 0.0,
        "by_level": by_level,
        "warning_count": warning_count,
        "schema_repair_warning_count": schema_repair_warning_count,
    }


def structured_output_markdown(payload: dict[str, Any]) -> str:
    if "summary" in payload:
        summary = payload["summary"]
        return "\n".join(
            [
                "# Structured Output Parser Summary",
                "",
                f"Cases: `{summary['case_count']}`",
                f"Strict parse success: `{summary['strict_parse_success_count']}` "
                f"({summary['strict_parse_success_rate']:.3f})",
                f"Fallback parse success: `{summary['fallback_parse_success_count']}` "
                f"({summary['fallback_parse_success_rate']:.3f})",
                f"Parse success: `{summary['parse_success_count']}`",
                f"Parse success rate: `{summary['parse_success_rate']:.3f}`",
                f"By level: `{summary['by_level']}`",
                f"Warnings: `{summary['warning_count']}`",
                f"Schema repair warnings: `{summary['schema_repair_warning_count']}`",
            ]
        )
    return "\n".join(
        [
            "# Structured Output Parser Trace",
            "",
            f"Case: `{payload['case_id']}`",
            f"Expected ok: `{payload['expected_ok']}`",
            f"Actual ok: `{payload['actual_ok']}`",
            f"Expected level: `{payload['expected_level']}`",
            f"Actual level: `{payload['actual_level']}`",
            f"Metadata: `{payload['metadata']}`",
            "",
            "## Parsed Data",
            "",
            "```json",
            json.dumps(payload["data"], ensure_ascii=False, indent=2),
            "```",
        ]
    )
