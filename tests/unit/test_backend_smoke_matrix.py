import json
import subprocess
import sys

import pytest

from deepresearch_agent.llm.smoke_matrix import run_backend_smoke_matrix


@pytest.mark.asyncio
async def test_backend_smoke_matrix_attempts_mock_only_by_default() -> None:
    payload = await run_backend_smoke_matrix(run_real=False)

    assert payload["attempted_count"] == 1
    assert payload["success_count"] == 1
    mock = next(row for row in payload["rows"] if row["backend"] == "mock")
    assert mock["success"] is True
    assert mock["smoke_attempted"] is True
    assert {row["backend"] for row in payload["rows"]} == {"mock", "openai", "deepseek", "vllm"}


def test_run_backend_smoke_matrix_cli_json() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_backend_smoke_matrix.py", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["attempted_count"] == 1
    assert any(row["backend"] == "deepseek" for row in payload["rows"])
