import json
import subprocess
import sys

from deepresearch_agent.orchestration.stress_cases import (
    get_orchestration_stress_case,
    load_orchestration_stress_cases,
    orchestration_stress_summary,
)


def test_orchestration_stress_cases_cover_three_fallback_levels() -> None:
    cases = load_orchestration_stress_cases()

    assert len(cases) == 6
    assert {case.run_summary["fallback_level"] for case in cases} == {1, 2, 3}
    assert get_orchestration_stress_case("batch_replan").run_summary["replan_count"] == 1
    assert "recovery" in get_orchestration_stress_case("batch_replan").after_graph


def test_orchestration_stress_summary_has_rates() -> None:
    summary = orchestration_stress_summary()

    assert summary["case_count"] == 6
    assert 0.0 <= summary["timeout_recovery_rate"] <= 1.0
    assert 0.0 <= summary["batch_replan_success_rate"] <= 1.0
    assert 0.0 <= summary["fallback_report_rate"] <= 1.0


def test_inspect_orchestration_stress_cli_json() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/inspect_orchestration_stress.py",
            "--case",
            "global_fallback",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["id"] == "global_fallback"
    assert payload["run_summary"]["fallback_report_rate"] == 1.0
