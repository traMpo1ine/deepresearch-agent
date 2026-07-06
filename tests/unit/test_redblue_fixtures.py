import json
from pathlib import Path

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


FIXTURE_PATH = Path("data/adversarial/redblue_fixtures.jsonl")


def load_fixtures() -> list[dict]:
    return [json.loads(line) for line in FIXTURE_PATH.read_text(encoding="utf-8").splitlines()]


@pytest.mark.asyncio
async def test_redblue_adversarial_fixtures_trigger_expected_actions() -> None:
    fixtures = load_fixtures()
    assert len(fixtures) >= 80
    assert all("failure_mode" in item for item in fixtures)
    assert all("expected_status_after_repair" in item for item in fixtures)
    assert all("expected_action" in item for item in fixtures)
    correct = 0
    observed_actions = set()
    for item in fixtures:
        claim = Claim(
            id=f"claim_{item['id']}",
            text=item["claim_text"],
            citation_ids=item["citation_ids"],
            verification_status=VerificationStatus(item["status"]),
        )
        report = ResearchReport("q", "t", "s", [claim], [])
        finding = AttackFinding(
            target_claim_id=claim.id if item["target_claim"] else None,
            category=AttackCategory(item["finding_category"]),
            severity=item.get("severity", 4),
            reason=item["reason"],
            suggested_check=item["expected_action"],
        )

        repaired = await BlueRepairAgent().repair(report, [finding])

        action = repaired.repair_actions[-1].action_type
        observed_actions.add(action)
        if action == RepairActionType(item["expected_action"]):
            correct += 1
    assert correct >= int(len(fixtures) * 0.9)
    assert observed_actions == {
        RepairActionType.ADD,
        RepairActionType.DELETE,
        RepairActionType.MODIFY,
        RepairActionType.VERIFY,
    }
