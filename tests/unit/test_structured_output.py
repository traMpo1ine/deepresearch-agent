import json
import subprocess
import sys

from deepresearch_agent.structured_output import StructuredOutputParser
from deepresearch_agent.structured_output_cases import (
    DEFAULT_SCHEMA,
    load_structured_output_cases,
    structured_output_summary,
)


def test_structured_output_parser_three_fallback_levels() -> None:
    parser = StructuredOutputParser()

    strict = parser.parse('{"title":"A","claims":[],"citations":[]}', DEFAULT_SCHEMA)
    fenced = parser.parse('```json\n{"title":"B","claims":[],"citations":[]}\n```', DEFAULT_SCHEMA)
    repaired = parser.parse("{title:'C', claims:['c'], citations:['ev'],}", DEFAULT_SCHEMA)
    defaulted = parser.parse("not json", DEFAULT_SCHEMA)

    assert strict.ok and strict.parse_level == 1
    assert fenced.ok and fenced.parse_level == 2
    assert repaired.ok and repaired.parse_level == 3
    assert defaulted.ok and defaulted.parse_level == 3
    assert defaulted.data["title"] == "Untitled"


def test_structured_output_cases_reach_expected_success_rate() -> None:
    cases = load_structured_output_cases()
    assert len(cases) >= 50

    parser = StructuredOutputParser()
    results = [parser.parse(case.text, DEFAULT_SCHEMA) for case in cases]

    assert all(result.ok for result in results)
    summary = structured_output_summary()
    assert summary["parse_success_rate"] == 1.0
    assert summary["strict_parse_success_count"] > 0
    assert summary["fallback_parse_success_count"] > 0
    assert summary["schema_repair_warning_count"] > 0
    assert {result.parse_level for result in results} == {1, 2, 3}


def test_inspect_structured_output_cli_json() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/inspect_structured_output.py",
            "--case",
            "combo_repair_001",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["actual_ok"] is True
    assert payload["actual_level"] == 3
    assert payload["data"]["title"] == "U"
