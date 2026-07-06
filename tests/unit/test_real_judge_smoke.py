import pytest

from deepresearch_agent.evaluation.real_judge_smoke import run_real_judge_smoke
from deepresearch_agent.llm import LLMBackendConfig


@pytest.mark.asyncio
async def test_real_judge_smoke_runs_with_mock_backend() -> None:
    payload = await run_real_judge_smoke(LLMBackendConfig(backend="mock"), limit=2)

    assert payload["attempted"] == 2
    assert payload["successful"] == 2
    assert payload["rows"][0]["scores"]["overall"] > 0
    assert "offline/mock ResearchBench metrics" in payload["boundary"]


@pytest.mark.asyncio
async def test_real_judge_smoke_skips_real_backend_without_run_real() -> None:
    payload = await run_real_judge_smoke(LLMBackendConfig(backend="deepseek"), limit=1)

    assert payload["attempted"] == 0
    assert payload["successful"] == 0
    assert payload["skipped_reason"]
