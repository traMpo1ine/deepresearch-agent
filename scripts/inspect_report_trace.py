from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_report_trace(report: dict[str, Any], claim_id: str | None = None) -> dict[str, Any]:
    evidence_by_id = {item["id"]: item for item in report.get("evidence", [])}
    repairs_by_target: dict[str, list[dict[str, Any]]] = {}
    for action in report.get("repair_actions", []):
        repairs_by_target.setdefault(action.get("target_claim_id", ""), []).append(action)

    claims = report.get("claims", [])
    selected = [claim for claim in claims if claim_id is None or claim.get("id") == claim_id]
    if claim_id is not None and not selected:
        raise ValueError(f"Claim id not found: {claim_id}")

    status_counts = Counter(claim.get("verification_status", "unknown") for claim in claims)
    claim_traces = [
        claim_trace(claim, evidence_by_id, repairs_by_target.get(claim.get("id", ""), []))
        for claim in selected
    ]
    cited_claims = sum(1 for claim in claims if claim.get("citation_ids"))
    return {
        "question": report.get("question"),
        "title": report.get("title"),
        "run_id": report.get("run_id"),
        "summary": {
            "claim_count": len(claims),
            "evidence_count": len(evidence_by_id),
            "repair_action_count": len(report.get("repair_actions", [])),
            "citation_coverage": cited_claims / len(claims) if claims else 0.0,
            "verification_status_counts": dict(status_counts),
        },
        "claims": claim_traces,
    }


def claim_trace(
    claim: dict[str, Any],
    evidence_by_id: dict[str, dict[str, Any]],
    repair_actions: list[dict[str, Any]],
) -> dict[str, Any]:
    citations = []
    for citation_id in claim.get("citation_ids", []):
        evidence = evidence_by_id.get(citation_id)
        citations.append(
            {
                "citation_id": citation_id,
                "found": evidence is not None,
                "title": evidence.get("title") if evidence else None,
                "source_id": evidence.get("source_id") if evidence else None,
                "chunk_id": evidence.get("chunk_id") if evidence else None,
                "quote": evidence.get("quote") if evidence else None,
                "score": evidence.get("score") if evidence else None,
            }
        )
    trace = claim.get("verification_trace") or {}
    atomic_results = [
        {
            "text": atomic.get("text"),
            "status": atomic.get("status"),
            "evidence_id": atomic.get("evidence_id"),
            "best_quote": atomic.get("best_quote"),
            "term_overlap": atomic.get("term_overlap"),
            "quote_overlap": atomic.get("quote_overlap"),
            "missing_terms": atomic.get("missing_terms", []),
            "decision_reason": atomic.get("decision_reason") or atomic.get("reason", ""),
        }
        for atomic in trace.get("atomic_results", [])
    ]
    return {
        "id": claim.get("id"),
        "text": claim.get("text"),
        "verification_status": claim.get("verification_status"),
        "confidence": claim.get("confidence"),
        "needs_verification": claim.get("needs_verification"),
        "verification_reason": claim.get("verification_reason"),
        "citation_ids": claim.get("citation_ids", []),
        "citations": citations,
        "trace": {
            "present": bool(trace),
            "status": trace.get("status"),
            "matched_evidence_ids": trace.get("matched_evidence_ids", []),
            "support_terms": trace.get("support_terms", []),
            "missing_terms": trace.get("missing_terms", []),
            "citation_presence": trace.get("citation_presence"),
            "term_overlap": trace.get("term_overlap"),
            "quote_overlap": trace.get("quote_overlap"),
            "contradiction_cues": trace.get("contradiction_cues", []),
            "reason": trace.get("reason", ""),
            "atomic_results": atomic_results,
        },
        "repair_actions": repair_actions,
    }


def payload_to_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# DeepResearch Report Trace",
        "",
        f"Title: {payload.get('title')}",
        f"Question: {payload.get('question')}",
        f"Run id: `{payload.get('run_id')}`",
        "",
        "## Summary",
        "",
        f"- Claims: `{summary['claim_count']}`",
        f"- Evidence: `{summary['evidence_count']}`",
        f"- Repair actions: `{summary['repair_action_count']}`",
        f"- Citation coverage: `{summary['citation_coverage']:.3f}`",
        f"- Verification status counts: `{summary['verification_status_counts']}`",
        "",
        "## Claim Traces",
        "",
    ]
    for index, claim in enumerate(payload["claims"], start=1):
        lines.extend(
            [
                f"### Claim {index}: `{claim['id']}`",
                "",
                claim.get("text") or "",
                "",
                f"- Status: `{claim.get('verification_status')}`",
                f"- Confidence: `{claim.get('confidence')}`",
                f"- Needs verification: `{claim.get('needs_verification')}`",
                f"- Reason: {claim.get('verification_reason')}",
                "",
                "#### Citations",
                "",
            ]
        )
        if not claim["citations"]:
            lines.append("- No citations.")
        for citation in claim["citations"]:
            if citation["found"]:
                lines.append(
                    f"- `{citation['citation_id']}` found | source={citation['source_id']} "
                    f"| chunk={citation['chunk_id']} | quote={citation['quote']}"
                )
            else:
                lines.append(f"- `{citation['citation_id']}` missing from report evidence.")
        trace = claim["trace"]
        lines.extend(["", "#### Verification Trace", ""])
        if not trace["present"]:
            lines.append("- No verification trace.")
        else:
            lines.extend(
                [
                    f"- Matched evidence ids: `{trace['matched_evidence_ids']}`",
                    f"- Support terms: `{trace['support_terms']}`",
                    f"- Missing terms: `{trace['missing_terms']}`",
                    f"- Term overlap: `{trace['term_overlap']}`",
                    f"- Quote overlap: `{trace['quote_overlap']}`",
                    f"- Contradiction cues: `{trace['contradiction_cues']}`",
                    f"- Reason: {trace['reason']}",
                    "",
                    "#### Atomic Results",
                    "",
                ]
            )
            if not trace["atomic_results"]:
                lines.append("- No atomic results.")
            for atomic in trace["atomic_results"]:
                lines.append(
                    f"- `{atomic['status']}` evidence={atomic['evidence_id']} "
                    f"term={atomic['term_overlap']} quote={atomic['quote_overlap']} "
                    f"missing={atomic['missing_terms']} reason={atomic['decision_reason']}"
                )
        lines.extend(["", "#### Repair Actions", ""])
        if not claim["repair_actions"]:
            lines.append("- No repair actions targeting this claim.")
        for action in claim["repair_actions"]:
            lines.append(
                f"- `{action.get('action_type')}` reason={action.get('reason')} "
                f"before={action.get('before')} after={action.get('after')}"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect claim-citation-verification traces in a report JSON.")
    parser.add_argument("--report-json", required=True, help="Path to a ResearchReport JSON file.")
    parser.add_argument("--claim-id", help="Only inspect one claim id.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    args = parser.parse_args()

    payload = build_report_trace(load_report(args.report_json), claim_id=args.claim_id)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload_to_markdown(payload))


if __name__ == "__main__":
    main()
