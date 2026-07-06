import json
import subprocess
import sys

import pytest

from deepresearch_agent.redblue_fixture_eval import evaluate_redblue_fixtures


@pytest.mark.asyncio
async def test_redblue_fixture_eval_reports_before_after_success() -> None:
    payload = await evaluate_redblue_fixtures()

    assert payload["case_count"] >= 80
    assert payload["repair_success_after"] > payload["repair_success_before"]
    assert payload["action_accuracy"] >= 0.9
    assert payload["repair_precision"] >= 0.9
    assert payload["repair_coverage"] >= 0.9
    assert {"add", "delete", "modify", "verify"} <= set(payload["action_distribution"])
    assert "overclaim" in payload["per_failure_mode"]
    assert payload["per_source_of_error"]


def test_run_redblue_eval_cli_json() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_redblue_eval.py", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["case_count"] >= 80
    assert payload["repair_success_delta"] > 0
