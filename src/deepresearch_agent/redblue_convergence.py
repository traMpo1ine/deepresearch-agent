from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from deepresearch_agent.schemas import RepairLoopTrace
from deepresearch_agent.schemas.serialization import to_jsonable


@dataclass(frozen=True, slots=True)
class RedBlueConvergenceCase:
    case_id: str
    description: str
    traces: list[RepairLoopTrace]


def load_convergence_cases() -> dict[str, RedBlueConvergenceCase]:
    return {
        "converged": RedBlueConvergenceCase(
            case_id="converged",
            description="Red finds no remaining issues after verification.",
            traces=[
                RepairLoopTrace(
                    round_index=0,
                    finding_count=0,
                    weak_claim_count=0,
                    repair_action_count=0,
                    claim_fingerprint_before="supported",
                    claim_fingerprint_after="supported",
                    converged=True,
                    stop_reason="CONVERGED",
                )
            ],
        ),
        "oscillation": RedBlueConvergenceCase(
            case_id="oscillation",
            description="Blue repeatedly modifies the same claim without improving the fingerprint.",
            traces=[
                RepairLoopTrace(
                    round_index=0,
                    finding_count=1,
                    weak_claim_count=1,
                    repair_action_count=1,
                    claim_fingerprint_before="claim_a_strong",
                    claim_fingerprint_after="claim_a_qualified",
                ),
                RepairLoopTrace(
                    round_index=1,
                    finding_count=1,
                    weak_claim_count=1,
                    repair_action_count=1,
                    claim_fingerprint_before="claim_a_qualified",
                    claim_fingerprint_after="claim_a_qualified",
                    oscillating=True,
                    stop_reason="OSCILLATION",
                ),
            ],
        ),
        "max_rounds": RedBlueConvergenceCase(
            case_id="max_rounds",
            description="The repair loop reaches the configured maximum round count.",
            traces=[
                RepairLoopTrace(
                    round_index=0,
                    finding_count=2,
                    weak_claim_count=2,
                    repair_action_count=2,
                    claim_fingerprint_before="round0",
                    claim_fingerprint_after="round1",
                ),
                RepairLoopTrace(
                    round_index=1,
                    finding_count=1,
                    weak_claim_count=1,
                    repair_action_count=1,
                    claim_fingerprint_before="round1",
                    claim_fingerprint_after="round2",
                    stop_reason="MAX_ROUNDS",
                ),
            ],
        ),
    }


def inspect_convergence_case(case_id: str) -> dict[str, Any]:
    cases = load_convergence_cases()
    if case_id not in cases:
        valid = ", ".join(sorted(cases))
        raise KeyError(f"Unknown convergence case: {case_id}. Valid cases: {valid}")
    case = cases[case_id]
    traces = [to_jsonable(trace) for trace in case.traces]
    return {
        "case_id": case.case_id,
        "description": case.description,
        "round_count": len(traces),
        "converged": any(trace["converged"] for trace in traces),
        "oscillating": any(trace["oscillating"] for trace in traces),
        "stop_reason": traces[-1]["stop_reason"] if traces else "NOT_RUN",
        "traces": traces,
    }


def convergence_payload_to_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Red-Blue Convergence Trace",
        "",
        f"Case: `{payload['case_id']}`",
        f"Description: {payload['description']}",
        f"Stop reason: `{payload['stop_reason']}`",
        f"Converged: `{str(payload['converged']).lower()}`",
        f"Oscillating: `{str(payload['oscillating']).lower()}`",
        "",
        "| round | findings | weak claims | actions | converged | oscillating | stop |",
        "|---:|---:|---:|---:|---|---|---|",
    ]
    for trace in payload["traces"]:
        lines.append(
            f"| {trace['round_index']} | {trace['finding_count']} | "
            f"{trace['weak_claim_count']} | {trace['repair_action_count']} | "
            f"{trace['converged']} | {trace['oscillating']} | {trace['stop_reason']} |"
        )
    return "\n".join(lines)


def payload_json(payload: dict[str, Any]) -> str:
    return json.dumps(to_jsonable(payload), ensure_ascii=False, indent=2)
