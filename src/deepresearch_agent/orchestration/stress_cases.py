from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class OrchestrationStressCase:
    id: str
    description: str
    task_trace: list[str]
    before_graph: str
    after_graph: str
    run_summary: dict[str, Any]
    learning_note: str


def load_orchestration_stress_cases() -> list[OrchestrationStressCase]:
    return [
        OrchestrationStressCase(
            id="task_timeout",
            description="A single search task times out and is marked as a timeout failure.",
            task_trace=["PENDING", "READY", "RUNNING", "TIMED_OUT", "FAILED"],
            before_graph="root --> search_timeout",
            after_graph="root --> search_timeout",
            run_summary={
                "fallback_level": 1,
                "timed_out_tasks": 1,
                "replan_count": 0,
                "timeout_recovery_rate": 0.0,
                "batch_replan_success_rate": 0.0,
                "fallback_report_rate": 0.0,
            },
            learning_note="Level 1 fallback is task-local timeout detection.",
        ),
        OrchestrationStressCase(
            id="retry_success",
            description="A timed-out task returns to READY and succeeds on retry.",
            task_trace=["PENDING", "READY", "RUNNING", "TIMED_OUT", "READY", "RUNNING", "VERIFIED"],
            before_graph="root --> search_retry",
            after_graph="root --> search_retry",
            run_summary={
                "fallback_level": 1,
                "timed_out_tasks": 1,
                "replan_count": 0,
                "timeout_recovery_rate": 1.0,
                "batch_replan_success_rate": 0.0,
                "fallback_report_rate": 0.0,
            },
            learning_note="Retries keep recovery local before touching the DAG.",
        ),
        OrchestrationStressCase(
            id="retry_exhausted",
            description="A timed-out task exhausts retries and fails.",
            task_trace=["PENDING", "READY", "RUNNING", "TIMED_OUT", "READY", "RUNNING", "TIMED_OUT", "FAILED"],
            before_graph="root --> search_exhausted --> synthesize",
            after_graph="root --> search_exhausted --> synthesize(blocked)",
            run_summary={
                "fallback_level": 1,
                "timed_out_tasks": 2,
                "replan_count": 0,
                "timeout_recovery_rate": 0.0,
                "batch_replan_success_rate": 0.0,
                "fallback_report_rate": 0.0,
            },
            learning_note="Exhausted retries become explicit failed tasks and can block dependents.",
        ),
        OrchestrationStressCase(
            id="batch_replan",
            description="A batch contains a failed task, so a recovery task is appended.",
            task_trace=["PENDING", "READY", "RUNNING", "FAILED", "READY", "RUNNING", "VERIFIED"],
            before_graph="root --> [search_a, search_b] --> synthesize",
            after_graph="root --> [search_a, search_b, recovery_search_b] --> synthesize",
            run_summary={
                "fallback_level": 2,
                "timed_out_tasks": 0,
                "replan_count": 1,
                "timeout_recovery_rate": 0.0,
                "batch_replan_success_rate": 1.0,
                "fallback_report_rate": 0.0,
            },
            learning_note="Level 2 replan appends recovery work instead of rewriting the whole DAG.",
        ),
        OrchestrationStressCase(
            id="evidence_insufficient",
            description="The pipeline finishes but has too little evidence for a normal report.",
            task_trace=["PENDING", "READY", "RUNNING", "VERIFIED"],
            before_graph="root --> search_low_evidence --> write",
            after_graph="root --> search_low_evidence --> fallback_write",
            run_summary={
                "fallback_level": 3,
                "timed_out_tasks": 0,
                "replan_count": 0,
                "timeout_recovery_rate": 0.0,
                "batch_replan_success_rate": 0.0,
                "fallback_report_rate": 1.0,
            },
            learning_note="Level 3 fallback produces a report with explicit limitations.",
        ),
        OrchestrationStressCase(
            id="global_fallback",
            description="Multiple failures leave insufficient evidence, so the writer emits fallback synthesis.",
            task_trace=["PENDING", "READY", "RUNNING", "FAILED", "BLOCKED", "REPAIRING", "VERIFIED"],
            before_graph="root --> [search_a, search_b] --> synthesize",
            after_graph="root --> fallback_synthesis",
            run_summary={
                "fallback_level": 3,
                "timed_out_tasks": 1,
                "replan_count": 1,
                "timeout_recovery_rate": 0.0,
                "batch_replan_success_rate": 0.0,
                "fallback_report_rate": 1.0,
            },
            learning_note="Global fallback keeps failure cases inspectable instead of hiding partial output.",
        ),
    ]


def get_orchestration_stress_case(case_id: str) -> OrchestrationStressCase:
    for case in load_orchestration_stress_cases():
        if case.id == case_id:
            return case
    available = ", ".join(case.id for case in load_orchestration_stress_cases())
    raise ValueError(f"Unknown orchestration stress case '{case_id}'. Available cases: {available}")


def orchestration_stress_summary() -> dict[str, Any]:
    cases = load_orchestration_stress_cases()
    return {
        "case_count": len(cases),
        "timeout_recovery_rate": sum(
            case.run_summary["timeout_recovery_rate"] for case in cases
        )
        / len(cases),
        "batch_replan_success_rate": sum(
            case.run_summary["batch_replan_success_rate"] for case in cases
        )
        / len(cases),
        "fallback_report_rate": sum(case.run_summary["fallback_report_rate"] for case in cases)
        / len(cases),
        "cases": [case.id for case in cases],
    }


def stress_case_to_dict(case: OrchestrationStressCase) -> dict[str, Any]:
    return {
        "id": case.id,
        "description": case.description,
        "task_trace": case.task_trace,
        "before_graph": case.before_graph,
        "after_graph": case.after_graph,
        "run_summary": case.run_summary,
        "learning_note": case.learning_note,
    }


def stress_markdown(payload: dict[str, Any]) -> str:
    if "summary" in payload:
        summary = payload["summary"]
        return "\n".join(
            [
                "# Orchestration Stress Summary",
                "",
                f"Cases: `{summary['case_count']}`",
                f"Mean timeout recovery rate: `{summary['timeout_recovery_rate']:.3f}`",
                f"Mean batch replan success rate: `{summary['batch_replan_success_rate']:.3f}`",
                f"Mean fallback report rate: `{summary['fallback_report_rate']:.3f}`",
                f"Cases: `{summary['cases']}`",
            ]
        )
    return "\n".join(
        [
            "# Orchestration Stress Case",
            "",
            f"Case: `{payload['id']}`",
            f"Description: {payload['description']}",
            f"Task trace: `{' -> '.join(payload['task_trace'])}`",
            "",
            "## DAG Before",
            "",
            f"`{payload['before_graph']}`",
            "",
            "## DAG After",
            "",
            f"`{payload['after_graph']}`",
            "",
            "## Run Summary",
            "",
            f"`{payload['run_summary']}`",
            "",
            "## Learning Note",
            "",
            payload["learning_note"],
        ]
    )
