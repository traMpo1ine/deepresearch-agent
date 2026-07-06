import pytest

from deepresearch_agent.redblue_cases import (
    expected_repair_action,
    get_redblue_case,
    inspect_redblue_case,
    load_redblue_cases,
)
from deepresearch_agent.schemas import RepairActionType


def test_load_redblue_cases_reads_learning_examples() -> None:
    cases = load_redblue_cases()

    assert {case.id for case in cases} == {
        "no_citation",
        "wrong_citation",
        "overclaim",
        "contradiction",
        "omission",
        "vague_claim",
        "supported_clean",
    }


@pytest.mark.asyncio
async def test_redblue_cases_produce_expected_actions() -> None:
    for case in load_redblue_cases():
        repaired, payload = await inspect_redblue_case(case)
        expected_action = expected_repair_action(case)

        if expected_action is None:
            assert not repaired.repair_actions
            assert payload["observed_action"] == "none"
        else:
            assert repaired.repair_actions[-1].action_type == expected_action
            assert payload["observed_action"] == expected_action.value


@pytest.mark.asyncio
async def test_overclaim_triggers_modify_action() -> None:
    repaired, payload = await inspect_redblue_case(get_redblue_case("overclaim"))

    assert repaired.repair_actions[-1].action_type == RepairActionType.MODIFY
    assert payload["repair_actions"][-1]["after"].startswith("Evidence suggests that ")


@pytest.mark.asyncio
async def test_unsupported_and_contradicted_cases_trigger_delete() -> None:
    for case_id in ["wrong_citation", "contradiction", "no_citation"]:
        repaired, payload = await inspect_redblue_case(get_redblue_case(case_id))

        assert repaired.repair_actions[-1].action_type == RepairActionType.DELETE
        assert payload["after_claims"] == {}


@pytest.mark.asyncio
async def test_omission_case_triggers_add_limitation() -> None:
    repaired, payload = await inspect_redblue_case(get_redblue_case("omission"))

    assert repaired.repair_actions[-1].action_type == RepairActionType.ADD
    assert repaired.limitations
    assert payload["limitations"]


@pytest.mark.asyncio
async def test_supported_clean_case_needs_no_repair() -> None:
    repaired, payload = await inspect_redblue_case(get_redblue_case("supported_clean"))

    assert not repaired.repair_actions
    assert payload["findings"] == []
    assert payload["observed_action"] == "none"
