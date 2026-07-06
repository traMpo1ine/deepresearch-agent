import importlib.util
import sys
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "check_project_completion",
    Path("scripts/check_project_completion.py"),
)
completion = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["check_project_completion"] = completion
spec.loader.exec_module(completion)


def test_completion_source_requirements_pass_for_current_project() -> None:
    payload = completion.build_completion_payload(completion.ROOT, include_generated=False)

    assert payload["status"] == "passed"
    assert payload["summary"]["path_missing"] == 0
    assert payload["summary"]["text_missing"] == 0


def test_completion_markdown_exposes_status_and_missing_sections() -> None:
    payload = {
        "status": "passed",
        "include_generated": False,
        "summary": {
            "path_total": 1,
            "path_missing": 0,
            "text_total": 1,
            "text_missing": 0,
        },
        "path_checks": [
            {
                "group": "project",
                "path": "README.md",
                "exists": True,
                "bytes": 10,
            }
        ],
        "text_checks": [
            {
                "path": "README.md",
                "phrase": "run_showcase.py",
                "present": True,
            }
        ],
    }

    markdown = completion.payload_to_markdown(payload)

    assert "Status: `passed`" in markdown
    assert "## Missing Paths" in markdown
    assert "`project`: 1/1 present" in markdown
