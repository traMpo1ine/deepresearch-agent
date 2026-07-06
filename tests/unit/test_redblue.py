import pytest

from deepresearch_agent.redblue import BlueRepairAgent
from deepresearch_agent.schemas import (
    AttackCategory,
    AttackFinding,
    Claim,
    RepairActionType,
    ResearchReport,
    VerificationStatus,
)


@pytest.mark.asyncio
async def test_blue_deletes_unsupported_claim() -> None:
    claim = Claim(
        id="claim_bad",
        text="The system is always perfectly factual.",
        citation_ids=["missing"],
        verification_status=VerificationStatus.UNSUPPORTED,
    )
    report = ResearchReport(
        question="q",
        title="t",
        summary="s",
        claims=[claim],
        evidence=[],
    )
    finding = AttackFinding(
        target_claim_id=claim.id,
        category=AttackCategory.FACTUALITY,
        severity=4,
        reason="Unsupported claim.",
        suggested_check="Delete it.",
    )

    repaired = await BlueRepairAgent().repair(report, [finding])

    assert not repaired.claims
    assert repaired.repair_actions[0].action_type == RepairActionType.DELETE


@pytest.mark.asyncio
async def test_blue_adds_limitation_for_omission() -> None:
    report = ResearchReport(question="q", title="t", summary="s", claims=[], evidence=[])
    finding = AttackFinding(
        target_claim_id=None,
        category=AttackCategory.OMISSION,
        severity=2,
        reason="Unused evidence.",
        suggested_check="Add limitation.",
    )

    repaired = await BlueRepairAgent().repair(report, [finding])

    assert repaired.limitations
    assert repaired.repair_actions[0].action_type == RepairActionType.ADD


@pytest.mark.asyncio
async def test_blue_dedupes_repeated_limitation_actions() -> None:
    report = ResearchReport(question="q", title="t", summary="s", claims=[], evidence=[])
    finding = AttackFinding(
        target_claim_id=None,
        category=AttackCategory.OMISSION,
        severity=2,
        reason="Unused evidence.",
        suggested_check="Add limitation.",
    )

    repaired = await BlueRepairAgent().repair(report, [finding, finding])

    assert len(repaired.limitations) == 1
    assert len(repaired.repair_actions) == 1
    assert repaired.repair_actions[0].action_type == RepairActionType.ADD


@pytest.mark.asyncio
async def test_blue_modify_preserves_leading_proper_noun_case() -> None:
    claim = Claim(
        id="claim_partial",
        text="SQLite-style local memory improves traceability.",
        citation_ids=["ev_1"],
        verification_status=VerificationStatus.PARTIAL,
    )
    report = ResearchReport(question="q", title="t", summary="s", claims=[claim], evidence=[])
    finding = AttackFinding(
        target_claim_id=claim.id,
        category=AttackCategory.FACTUALITY,
        severity=2,
        reason="Partially supported claim.",
        suggested_check="Qualify it.",
    )

    repaired = await BlueRepairAgent().repair(report, [finding])

    assert repaired.claims[0].text == "Evidence suggests that SQLite-style local memory improves traceability."
    assert repaired.repair_actions[0].action_type == RepairActionType.MODIFY
