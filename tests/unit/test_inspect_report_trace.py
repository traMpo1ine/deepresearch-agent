import importlib.util
import sys
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "inspect_report_trace",
    Path("scripts/inspect_report_trace.py"),
)
inspect_report_trace = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["inspect_report_trace"] = inspect_report_trace
spec.loader.exec_module(inspect_report_trace)


def sample_report() -> dict:
    return {
        "question": "Why verify citations?",
        "title": "Trace Report",
        "run_id": "run_trace",
        "claims": [
            {
                "id": "claim_a",
                "text": "Citation verification improves traceability.",
                "citation_ids": ["ev_a"],
                "verification_status": "supported",
                "confidence": 0.8,
                "needs_verification": False,
                "verification_reason": "Matched traceability.",
                "verification_trace": {
                    "status": "supported",
                    "matched_evidence_ids": ["ev_a"],
                    "support_terms": ["citation", "traceability"],
                    "missing_terms": [],
                    "citation_presence": True,
                    "term_overlap": 1.0,
                    "quote_overlap": 0.5,
                    "contradiction_cues": [],
                    "reason": "Supported by evidence.",
                    "atomic_results": [
                        {
                            "text": "Citation verification improves traceability",
                            "status": "supported",
                            "evidence_id": "ev_a",
                            "best_quote": "Citation verification links claims to evidence.",
                            "term_overlap": 1.0,
                            "quote_overlap": 0.5,
                            "missing_terms": [],
                            "decision_reason": "Best evidence=ev_a.",
                        }
                    ],
                },
            }
        ],
        "evidence": [
            {
                "id": "ev_a",
                "source_id": "source_a",
                "chunk_id": "source_a#1",
                "title": "Citation Verification",
                "quote": "Citation verification links claims to evidence.",
                "score": 0.9,
            }
        ],
        "repair_actions": [
            {
                "action_type": "verify",
                "target_claim_id": "claim_a",
                "reason": "Claim is supported.",
                "before": None,
                "after": None,
            }
        ],
    }


def test_report_trace_links_claim_to_citation_trace_and_repair() -> None:
    payload = inspect_report_trace.build_report_trace(sample_report())
    claim = payload["claims"][0]

    assert payload["summary"]["claim_count"] == 1
    assert payload["summary"]["citation_coverage"] == 1.0
    assert claim["citations"][0]["found"] is True
    assert claim["citations"][0]["quote"] == "Citation verification links claims to evidence."
    assert claim["trace"]["atomic_results"][0]["evidence_id"] == "ev_a"
    assert claim["repair_actions"][0]["action_type"] == "verify"


def test_report_trace_filters_by_claim_id() -> None:
    payload = inspect_report_trace.build_report_trace(sample_report(), claim_id="claim_a")

    assert len(payload["claims"]) == 1
    assert payload["claims"][0]["id"] == "claim_a"


def test_report_trace_markdown_contains_citation_and_atomic_sections() -> None:
    markdown = inspect_report_trace.payload_to_markdown(
        inspect_report_trace.build_report_trace(sample_report())
    )

    assert "DeepResearch Report Trace" in markdown
    assert "#### Citations" in markdown
    assert "#### Atomic Results" in markdown
    assert "`ev_a` found" in markdown
