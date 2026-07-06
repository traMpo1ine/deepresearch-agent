import importlib.util
import json
from pathlib import Path

import pytest

from deepresearch_agent.evaluation.llm_verifier_smoke import (
    ALLOWED_STATUSES,
    _load_cases,
    VerifierSmokeConfig,
    run_llm_verifier_smoke,
)

BUILDER_PATH = Path(__file__).resolve().parents[2] / "scripts" / "build_llm_verifier_extended_cases.py"
BUILDER_SPEC = importlib.util.spec_from_file_location("build_llm_verifier_extended_cases", BUILDER_PATH)
assert BUILDER_SPEC and BUILDER_SPEC.loader
builder = importlib.util.module_from_spec(BUILDER_SPEC)
BUILDER_SPEC.loader.exec_module(builder)
build_cases = builder.build_cases


@pytest.mark.asyncio
async def test_llm_verifier_smoke_dry_run_skips_real_provider(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    payload = await run_llm_verifier_smoke(
        VerifierSmokeConfig(
            output_path=tmp_path / "llm_verifier_smoke.md",
            run_real=False,
            limit=3,
        )
    )

    assert payload["summary"]["case_count"] == 3
    assert payload["summary"]["llm_attempted"] == 0
    assert payload["summary"]["estimated_cost_rmb"] == 0.0
    assert all(row["llm_status"] == "skipped" for row in payload["rows"])


@pytest.mark.asyncio
async def test_llm_verifier_smoke_writes_markdown(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    output = tmp_path / "smoke.md"
    output_json = tmp_path / "smoke.json"

    payload = await run_llm_verifier_smoke(
        VerifierSmokeConfig(output_path=output, output_json_path=output_json, limit=2)
    )

    text = output.read_text(encoding="utf-8")
    saved = json.loads(output_json.read_text(encoding="utf-8"))
    assert "# LLM Verifier Smoke" in text
    assert "heuristic_accuracy" in text
    assert "Confusion Matrix" in text
    assert "LLM verifier smoke is a provider/second-layer check" in text
    assert payload["summary"]["confusion_matrix"]
    assert payload["summary"]["per_expected_status"]
    assert saved["summary"]["case_count"] == 2


def test_llm_verifier_cases_have_minimum_status_coverage() -> None:
    cases = _load_cases(VerifierSmokeConfig().cases_path)
    statuses = {case["expected_status"] for case in cases}

    assert len(cases) >= 30
    assert statuses <= ALLOWED_STATUSES
    assert {"supported", "partial", "contradicted"} <= statuses


def test_extended_llm_verifier_cases_are_balanced() -> None:
    cases = _load_cases(VerifierSmokeConfig().cases_path.parent / "llm_verifier_cases_extended.jsonl")
    generated = build_cases()
    counts = {status: 0 for status in ALLOWED_STATUSES}
    for case in cases:
        counts[case["expected_status"]] += 1

    assert len(cases) == 120
    assert cases == generated
    assert counts == {
        "supported": 30,
        "partial": 30,
        "unsupported": 30,
        "contradicted": 30,
    }
