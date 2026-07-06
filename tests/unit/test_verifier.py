import pytest

from deepresearch_agent.agents.verifier import VerifierAgent
from deepresearch_agent.schemas import Claim, Evidence, VerificationStatus


@pytest.mark.asyncio
async def test_verifier_marks_uncited_claim_unsupported() -> None:
    claim = Claim(text="Agents always produce perfect reports.", citation_ids=[])

    verified = await VerifierAgent().verify(claim, [])

    assert verified.verification_status == VerificationStatus.UNSUPPORTED


@pytest.mark.asyncio
async def test_verifier_uses_cited_evidence() -> None:
    evidence = Evidence(
        id="ev_test",
        task_id="task",
        title="Citation tracking",
        text="Citation tracking binds claims to inspectable evidence and source chunks.",
        quote="Citation tracking binds claims to inspectable evidence.",
    )
    claim = Claim(
        text="Citation tracking binds claims to inspectable evidence.",
        citation_ids=["ev_test"],
    )

    verified = await VerifierAgent().verify(claim, [evidence])

    assert verified.verification_status in {VerificationStatus.SUPPORTED, VerificationStatus.PARTIAL}
    assert verified.matched_evidence_ids == ["ev_test"]
    assert verified.verification_trace is not None
    assert verified.verification_trace.citation_presence
    assert verified.verification_trace.term_overlap > 0


@pytest.mark.asyncio
async def test_verifier_selects_best_evidence_for_atomic_claim() -> None:
    weak = Evidence(
        id="ev_weak",
        task_id="task",
        title="Generic note",
        text="Research systems can use many engineering components.",
        quote="Many components can be useful.",
        metadata={"trust_level": "medium"},
    )
    strong = Evidence(
        id="ev_strong",
        task_id="task",
        title="SQLite memory",
        text="SQLite memory stores agent traces for later inspection.",
        quote="SQLite memory stores agent traces.",
        metadata={"trust_level": "high"},
    )
    claim = Claim(
        text="SQLite memory stores agent traces.",
        citation_ids=["ev_weak", "ev_strong"],
    )

    verified = await VerifierAgent().verify(claim, [weak, strong])

    assert verified.verification_trace is not None
    atomic = verified.verification_trace.atomic_results[0]
    assert atomic.evidence_id == "ev_strong"
    assert atomic.best_quote == "SQLite memory stores agent traces."
    assert atomic.evidence_scores[0]["evidence_id"] == "ev_strong"
    assert atomic.decision_reason


@pytest.mark.asyncio
async def test_verifier_marks_contradicted_atomic_claim() -> None:
    evidence = Evidence(
        id="ev_truth",
        task_id="task",
        title="Verifier limits",
        text="Verifier heuristics can reduce hallucinations but do not guarantee perfect truth.",
        quote="They do not guarantee perfect truth.",
    )
    claim = Claim(
        text="Verifier heuristics guarantee perfect truth.",
        citation_ids=["ev_truth"],
    )

    verified = await VerifierAgent().verify(claim, [evidence])

    assert verified.verification_status == VerificationStatus.CONTRADICTED
    assert verified.verification_trace is not None
    assert verified.verification_trace.atomic_results[0].contradiction_cues


@pytest.mark.asyncio
async def test_verifier_aggregates_mixed_atomic_claims_as_partial() -> None:
    evidence = Evidence(
        id="ev_one",
        task_id="task",
        title="Citation tracking",
        text="Citation tracking binds claims to evidence.",
        quote="Citation tracking binds claims to evidence.",
    )
    claim = Claim(
        text="Citation tracking binds claims to evidence and vector search guarantees perfect recall.",
        citation_ids=["ev_one"],
    )

    verified = await VerifierAgent().verify(claim, [evidence])

    assert verified.verification_status == VerificationStatus.PARTIAL
    assert verified.verification_trace is not None
    statuses = {result.status for result in verified.verification_trace.atomic_results}
    assert VerificationStatus.SUPPORTED in statuses
    assert VerificationStatus.UNSUPPORTED in statuses
