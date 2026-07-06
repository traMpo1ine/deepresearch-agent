import pytest

from deepresearch_agent.schemas import VerificationStatus
from deepresearch_agent.verification_cases import (
    get_verification_case,
    inspect_verification_case,
    load_verification_cases,
)


def test_load_verification_cases_reads_all_learning_examples() -> None:
    cases = load_verification_cases()

    assert {case.id for case in cases} == {
        "supported",
        "partial",
        "unsupported",
        "contradicted",
        "mixed_atomic",
        "no_citation",
    }


@pytest.mark.asyncio
async def test_verification_cases_match_expected_statuses() -> None:
    for case in load_verification_cases():
        verified, payload = await inspect_verification_case(case)

        assert verified.verification_status == case.expected_status
        assert payload["actual_status"] == case.expected_status.value
        assert payload["atomic_results"]


@pytest.mark.asyncio
async def test_mixed_atomic_case_contains_supported_and_unsupported_results() -> None:
    case = get_verification_case("mixed_atomic")
    verified, _payload = await inspect_verification_case(case)

    assert verified.verification_trace is not None
    statuses = {result.status for result in verified.verification_trace.atomic_results}
    assert VerificationStatus.SUPPORTED in statuses
    assert VerificationStatus.UNSUPPORTED in statuses
    assert verified.verification_status == VerificationStatus.PARTIAL


@pytest.mark.asyncio
async def test_contradicted_case_exposes_contradiction_cue() -> None:
    case = get_verification_case("contradicted")
    verified, _payload = await inspect_verification_case(case)

    assert verified.verification_trace is not None
    assert verified.verification_status == VerificationStatus.CONTRADICTED
    assert verified.verification_trace.atomic_results[0].contradiction_cues


@pytest.mark.asyncio
async def test_no_citation_case_has_no_citation_presence() -> None:
    case = get_verification_case("no_citation")
    verified, payload = await inspect_verification_case(case)

    assert verified.verification_trace is not None
    assert verified.verification_status == VerificationStatus.UNSUPPORTED
    assert not verified.verification_trace.citation_presence
    assert payload["citation_presence"] is False
