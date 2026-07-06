from __future__ import annotations

import argparse
import json


def build_case(case_id: str) -> dict:
    if case_id == "task_timeout":
        return {
            "case_id": "task_timeout",
            "description": "A running task exceeds timeout_seconds and enters TIMED_OUT before retry.",
            "task_trace": [
                "PENDING",
                "READY",
                "RUNNING",
                "TIMED_OUT",
                "READY",
                "RUNNING",
                "FAILED",
            ],
            "fallback_level": 1,
            "replan_count": 0,
            "learning_note": "Level 1 fallback is task-local timeout/retry handling.",
        }
    if case_id == "batch_replan":
        return {
            "case_id": "batch_replan",
            "description": "A topological batch has failed tasks, so the coordinator records a lightweight replan event.",
            "task_trace": ["PENDING", "READY", "RUNNING", "FAILED", "READY", "RUNNING", "VERIFIED"],
            "fallback_level": 2,
            "replan_count": 1,
            "batch_failure_events": [
                {
                    "batch_task_ids": ["task_a", "task_b"],
                    "failed_task_ids": ["task_b"],
                    "replan_index": 1,
                }
            ],
            "learning_note": "Level 2 fallback appends recovery work instead of rewriting the whole DAG.",
        }
    if case_id == "global_fallback":
        return {
            "case_id": "global_fallback",
            "description": "Evidence is below threshold, so Writer emits a report with explicit limitations.",
            "task_trace": ["PENDING", "READY", "RUNNING", "SUCCEEDED", "VERIFIED"],
            "fallback_level": 3,
            "replan_count": 0,
            "limitations": [
                "Fallback synthesis was used because retrieved evidence was below the configured threshold."
            ],
            "learning_note": "Level 3 fallback keeps the pipeline observable even when evidence is insufficient.",
        }
    raise SystemExit(f"Unknown case: {case_id}")


def payload_to_markdown(payload: dict) -> str:
    lines = [
        "# Orchestration Failure Trace",
        "",
        f"Case: `{payload['case_id']}`",
        f"Description: {payload['description']}",
        f"Fallback level: `{payload['fallback_level']}`",
        f"Replan count: `{payload['replan_count']}`",
        "",
        "## Task Trace",
        "",
        " -> ".join(f"`{status}`" for status in payload["task_trace"]),
        "",
        "## Learning Note",
        "",
        payload["learning_note"],
    ]
    if payload.get("batch_failure_events"):
        lines.extend(["", "## Batch Failure Events", ""])
        for event in payload["batch_failure_events"]:
            lines.append(f"- `{event}`")
    if payload.get("limitations"):
        lines.extend(["", "## Limitations", ""])
        for limitation in payload["limitations"]:
            lines.append(f"- {limitation}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect orchestration timeout/replan/fallback examples.")
    parser.add_argument("--case", choices=["task_timeout", "batch_replan", "global_fallback"], default="task_timeout")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    args = parser.parse_args()
    payload = build_case(args.case)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload_to_markdown(payload))


if __name__ == "__main__":
    main()
