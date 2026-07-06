from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deepresearch_agent.redblue import BlueRepairAgent, RedAgent
from deepresearch_agent.schemas import Claim, Evidence, RepairActionType, ResearchReport, VerificationStatus
from deepresearch_agent.schemas.serialization import to_jsonable


DEFAULT_REDBLUE_CASES_PATH = Path("data/examples/redblue_cases.jsonl")


@dataclass(slots=True)
class RedBlueCase:
    id: str
    question: str
    claims: list[Claim]
    evidence: list[Evidence]
    expected_action: str
    learning_note: str

    def to_report(self) -> ResearchReport:
        return ResearchReport(
            question=self.question,
            title=f"Red-Blue case: {self.id}",
            summary="Fixed learning case for Red-Blue observability.",
            claims=[
                Claim(
                    id=claim.id,
                    text=claim.text,
                    citation_ids=list(claim.citation_ids),
                    verification_status=claim.verification_status,
                    confidence=claim.confidence,
                    needs_verification=claim.needs_verification,
                    verification_reason=claim.verification_reason,
                    matched_evidence_ids=list(claim.matched_evidence_ids),
                    missing_terms=list(claim.missing_terms),
                    verification_trace=claim.verification_trace,
                )
                for claim in self.claims
            ],
            evidence=list(self.evidence),
        )


def load_redblue_cases(path: str | Path = DEFAULT_REDBLUE_CASES_PATH) -> list[RedBlueCase]:
    cases: list[RedBlueCase] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        cases.append(_case_from_raw(json.loads(line), line_number))
    return cases


def get_redblue_case(case_id: str, path: str | Path = DEFAULT_REDBLUE_CASES_PATH) -> RedBlueCase:
    cases = load_redblue_cases(path)
    for case in cases:
        if case.id == case_id:
            return case
    available = ", ".join(case.id for case in cases)
    raise ValueError(f"Unknown Red-Blue case '{case_id}'. Available cases: {available}")


async def inspect_redblue_case(case: RedBlueCase) -> tuple[ResearchReport, dict[str, Any]]:
    report = case.to_report()
    before_claims = {claim.id: claim.text for claim in report.claims}
    findings = await RedAgent().review(report)
    repaired = await BlueRepairAgent().repair(report, findings)
    return repaired, redblue_payload(case, before_claims, findings, repaired)


def redblue_payload(
    case: RedBlueCase,
    before_claims: dict[str, str],
    findings: list[Any],
    repaired: ResearchReport,
) -> dict[str, Any]:
    actions = repaired.repair_actions
    observed_action = actions[-1].action_type.value if actions else "none"
    return {
        "case_id": case.id,
        "question": case.question,
        "learning_note": case.learning_note,
        "expected_action": case.expected_action,
        "observed_action": observed_action,
        "findings": [
            {
                "target_claim_id": finding.target_claim_id,
                "category": finding.category.value,
                "severity": finding.severity,
                "reason": finding.reason,
                "suggested_check": finding.suggested_check,
            }
            for finding in findings
        ],
        "repair_actions": [
            {
                "action_type": action.action_type.value,
                "target_claim_id": action.target_claim_id,
                "reason": action.reason,
                "patch": action.patch,
                "before": action.before,
                "after": action.after,
            }
            for action in actions
        ],
        "before_claims": before_claims,
        "after_claims": {claim.id: claim.text for claim in repaired.claims},
        "limitations": repaired.limitations,
    }


def redblue_payload_to_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Red-Blue Trace",
        "",
        f"Case: `{payload['case_id']}`",
        "",
        f"Question: {payload['question']}",
        "",
        f"Expected action: `{payload['expected_action']}`",
        f"Observed action: `{payload['observed_action']}`",
        "",
        "## Learning Note",
        "",
        payload["learning_note"],
        "",
        "## Red Findings",
        "",
    ]
    if payload["findings"]:
        for index, finding in enumerate(payload["findings"], start=1):
            lines.extend(
                [
                    f"### Finding {index}",
                    "",
                    f"Target: `{finding['target_claim_id']}`",
                    f"Category: `{finding['category']}`",
                    f"Severity: `{finding['severity']}`",
                    f"Reason: {finding['reason']}",
                    f"Suggested check: {finding['suggested_check']}",
                    "",
                ]
            )
    else:
        lines.extend(["No Red finding was produced.", ""])
    lines.extend(["## Blue Repair Actions", ""])
    if payload["repair_actions"]:
        for index, action in enumerate(payload["repair_actions"], start=1):
            lines.extend(
                [
                    f"### Action {index}",
                    "",
                    f"Action: `{action['action_type']}`",
                    f"Target: `{action['target_claim_id']}`",
                    f"Reason: {action['reason']}",
                    f"Patch: {action['patch']}",
                    f"Before: {action['before']}",
                    f"After: {action['after']}",
                    "",
                ]
            )
    else:
        lines.extend(["No Blue repair action was needed.", ""])
    lines.extend(["## Claims", ""])
    lines.append(f"Before: `{payload['before_claims']}`")
    lines.append(f"After: `{payload['after_claims']}`")
    if payload["limitations"]:
        lines.extend(["", "## Limitations", ""])
        for limitation in payload["limitations"]:
            lines.append(f"- {limitation}")
    return "\n".join(lines)


def list_redblue_cases_markdown(cases: list[RedBlueCase]) -> str:
    lines = ["# Red-Blue Cases", ""]
    for case in cases:
        lines.append(f"- `{case.id}`: expected `{case.expected_action}` - {case.learning_note}")
    return "\n".join(lines)


def payload_json(payload: dict[str, Any]) -> str:
    return json.dumps(to_jsonable(payload), ensure_ascii=False, indent=2)


def _case_from_raw(raw: dict[str, Any], line_number: int) -> RedBlueCase:
    required = {"id", "question", "claims", "evidence", "expected_action", "learning_note"}
    missing = sorted(required - set(raw))
    if missing:
        raise ValueError(f"Red-Blue case line {line_number} is missing fields: {missing}")
    return RedBlueCase(
        id=str(raw["id"]),
        question=str(raw["question"]),
        claims=[
            Claim(
                id=str(item["id"]),
                text=str(item["text"]),
                citation_ids=[str(cid) for cid in item.get("citation_ids", [])],
                verification_status=VerificationStatus(str(item.get("verification_status", "unknown"))),
                confidence=float(item.get("confidence", 0.0)),
            )
            for item in raw["claims"]
        ],
        evidence=[Evidence(**item) for item in raw["evidence"]],
        expected_action=str(raw["expected_action"]),
        learning_note=str(raw["learning_note"]),
    )


def expected_repair_action(case: RedBlueCase) -> RepairActionType | None:
    return None if case.expected_action == "none" else RepairActionType(case.expected_action)
