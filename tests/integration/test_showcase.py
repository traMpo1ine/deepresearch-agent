import json

import pytest

from deepresearch_agent.showcase import build_showcase


@pytest.mark.asyncio
async def test_showcase_pack_generates_full_artifact_set(tmp_path) -> None:
    result = await build_showcase(
        question="Why should DeepResearch Agent verify citations?",
        output_dir=tmp_path / "showcase",
        max_concurrency=2,
    )

    expected_files = {
        "plan_md",
        "report_md",
        "report_json",
        "run_summary_json",
        "memory_trace_md",
        "compression_trace_md",
        "verifier_trace_md",
        "redblue_trace_md",
        "llm_backend_md",
        "eval_summary_md",
        "interview_notes_md",
        "index_md",
    }
    assert set(result.files) == expected_files
    for path in result.files.values():
        assert path.exists()
        assert path.read_text(encoding="utf-8").strip()

    report_payload = json.loads(result.files["report_json"].read_text(encoding="utf-8"))
    summary_payload = json.loads(result.files["run_summary_json"].read_text(encoding="utf-8"))
    index_text = result.files["index_md"].read_text(encoding="utf-8")

    assert report_payload["claims"]
    assert summary_payload["task_count"] >= 5
    assert summary_payload["llm_status"]["backend"] == "mock"
    assert "DeepResearch Showcase Pack" in index_text
    assert "verifier_trace.md" in index_text
    assert "llm_backend.md" in index_text
