from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deepresearch_agent.agents.verifier import VerifierAgent
from deepresearch_agent.schemas import Claim, Evidence, VerificationStatus
from deepresearch_agent.schemas.serialization import to_jsonable


DEFAULT_CASES_PATH = Path("data/examples/verification_cases.jsonl")


@dataclass(slots=True)
class VerificationCase:
    id: str
    claim: str
    evidence: list[Evidence]
    citation_ids: list[str]
    expected_status: VerificationStatus
    learning_note: str

    def to_claim(self) -> Claim:
        return Claim(text=self.claim, citation_ids=list(self.citation_ids))


def load_verification_cases(path: str | Path = DEFAULT_CASES_PATH) -> list[VerificationCase]:
    cases: list[VerificationCase] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        raw = json.loads(line)
        cases.append(_case_from_raw(raw, line_number))
    return cases


def get_verification_case(
    case_id: str,
    path: str | Path = DEFAULT_CASES_PATH,
) -> VerificationCase:
    cases = load_verification_cases(path)
    for case in cases:
        if case.id == case_id:
            return case
    available = ", ".join(case.id for case in cases)
    raise ValueError(f"Unknown verification case '{case_id}'. Available cases: {available}")


async def inspect_verification_case(case: VerificationCase) -> tuple[Claim, dict[str, Any]]:
    verified = await VerifierAgent().verify(case.to_claim(), case.evidence)
    return verified, verification_payload(case, verified)


def verification_payload(case: VerificationCase, verified: Claim) -> dict[str, Any]:
    trace = verified.verification_trace
    atomic_results = trace.atomic_results if trace else []
    return {
        "case_id": case.id,
        "claim": case.claim,
        "learning_note": case.learning_note,
        "expected_status": case.expected_status.value,
        "actual_status": verified.verification_status.value,
        "citation_ids": case.citation_ids,
        "citation_presence": trace.citation_presence if trace else False,
        "verification_reason": verified.verification_reason,
        "atomic_claims": trace.atomic_claims if trace else [],
        "atomic_results": [
            {
                "text": result.text,
                "status": result.status.value,
                "best_evidence": result.evidence_id,
                "best_quote": result.best_quote,
                "term_overlap": result.term_overlap,
                "quote_overlap": result.quote_overlap,
                "support_terms": result.support_terms,
                "missing_terms": result.missing_terms,
                "contradiction_cues": result.contradiction_cues,
                "decision_reason": result.decision_reason,
                "evidence_scores": result.evidence_scores,
            }
            for result in atomic_results
        ],
    }


def verification_payload_to_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Verification Trace",
        "",
        f"Case: `{payload['case_id']}`",
        "",
        f"Claim: {payload['claim']}",
        "",
        f"Expected status: `{payload['expected_status']}`",
        f"Actual status: `{payload['actual_status']}`",
        f"Citation presence: `{str(payload['citation_presence']).lower()}`",
        "",
        "## Learning Note",
        "",
        payload["learning_note"],
        "",
        "## Verification Reason",
        "",
        payload["verification_reason"],
        "",
        "## Atomic Results",
        "",
    ]
    for index, result in enumerate(payload["atomic_results"], start=1):
        lines.extend(
            [
                f"### Atomic {index}",
                "",
                f"Text: {result['text']}",
                f"Status: `{result['status']}`",
                f"Best evidence: `{result['best_evidence']}`",
                f"Best quote: {result['best_quote']}",
                f"Term overlap: `{result['term_overlap']:.2f}`",
                f"Quote overlap: `{result['quote_overlap']:.2f}`",
                f"Missing terms: `{result['missing_terms']}`",
                f"Contradiction cues: `{result['contradiction_cues']}`",
                "",
                f"Decision reason: {result['decision_reason']}",
                "",
            ]
        )
    return "\n".join(lines)


def list_cases_markdown(cases: list[VerificationCase]) -> str:
    lines = ["# Verification Cases", ""]
    for case in cases:
        lines.append(f"- `{case.id}`: expected `{case.expected_status.value}` - {case.learning_note}")
    return "\n".join(lines)


def _case_from_raw(raw: dict[str, Any], line_number: int) -> VerificationCase:
    required = {"id", "claim", "evidence", "citation_ids", "expected_status", "learning_note"}
    missing = sorted(required - set(raw))
    if missing:
        raise ValueError(f"Verification case line {line_number} is missing fields: {missing}")
    return VerificationCase(
        id=str(raw["id"]),
        claim=str(raw["claim"]),
        evidence=[Evidence(**item) for item in raw["evidence"]],
        citation_ids=[str(item) for item in raw["citation_ids"]],
        expected_status=VerificationStatus(str(raw["expected_status"])),
        learning_note=str(raw["learning_note"]),
    )


def payload_json(payload: dict[str, Any]) -> str:
    return json.dumps(to_jsonable(payload), ensure_ascii=False, indent=2)
