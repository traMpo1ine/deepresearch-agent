import pytest

from deepresearch_agent.agents.writer import WriterAgent
from deepresearch_agent.claim_preflight import ClaimPreflight
from deepresearch_agent.schemas import Claim, Evidence, VerificationStatus


def test_claim_preflight_dedupes_conflicts_and_downgrades_overclaim() -> None:
    claims = [
        Claim("The system always removes hallucination.", [], confidence=0.9),
        Claim("The system always removes hallucination.", [], confidence=0.9),
    ]
    evidence = [
        Evidence(
            id="ev_conflict",
            task_id="task",
            title="Conflict note",
            text="However, this method cannot guarantee perfect factuality.",
        )
    ]

    report = ClaimPreflight().run(claims, evidence)

    assert len(claims) == 1
    assert report.duplicate_claim_ids
    assert report.conflict_evidence_ids == ["ev_conflict"]
    assert report.downgraded_claim_ids == [claims[0].id]
    assert claims[0].verification_status == VerificationStatus.PARTIAL
    assert claims[0].needs_verification is True


@pytest.mark.asyncio
async def test_writer_records_claim_preflight_summary() -> None:
    report = await WriterAgent().write(
        "Why should claims be checked?",
        [
            Evidence(
                id="ev_conflict",
                task_id="task",
                title="Conflict note",
                text="However, fallback reports cannot guarantee complete coverage.",
                quote="fallback reports cannot guarantee complete coverage",
                score=1.0,
            )
        ],
    )

    assert "claim_preflight" in report.run_summary
    assert report.run_summary["claim_preflight"]["conflict_evidence_ids"] == ["ev_conflict"]
