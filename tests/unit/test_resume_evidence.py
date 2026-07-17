import json
import subprocess
import sys
from pathlib import Path

from deepresearch_agent.resume_evidence import (
    build_resume_evidence_payload,
    get_resume_evidence,
    payload_to_markdown,
)


def test_resume_evidence_has_expected_bullets_and_boundaries() -> None:
    payload = build_resume_evidence_payload(root=Path.cwd())

    assert payload["count"] == 9
    ids = {entry["evidence_id"] for entry in payload["entries"]}
    assert ids == {
        "orchestration",
        "memory_vector",
        "compression",
        "verifier_redblue",
        "structured_preflight",
        "evaluation",
        "corpus_profiles",
        "llm_verifier_smoke",
        "demo_app",
    }
    assert all(entry["boundary"] for entry in payload["entries"])
    assert all(entry["learning_story"] for entry in payload["entries"])


def test_resume_evidence_paths_are_real_project_evidence() -> None:
    payload = build_resume_evidence_payload(root=Path.cwd())
    checks = [
        check
        for entry in payload["entries"]
        for check in entry["path_checks"]
    ]

    assert checks
    assert all(check["exists"] for check in checks), [
        check["path"] for check in checks if not check["exists"]
    ]
    tracked = set(
        subprocess.run(
            ["git", "ls-files"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    )
    assert all(check["path"] in tracked for check in checks), [
        check["path"] for check in checks if check["path"] not in tracked
    ]


def test_resume_evidence_markdown_is_study_friendly() -> None:
    payload = build_resume_evidence_payload("verifier_redblue", root=Path.cwd())
    markdown = payload_to_markdown(payload)

    assert "Resume Evidence Traceability" in markdown
    assert "Verifier + Red-Blue" in markdown
    assert "Learning story" in markdown
    assert "Boundary" in markdown


def test_resume_evidence_unknown_id_is_explicit() -> None:
    try:
        get_resume_evidence("missing")
    except KeyError as exc:
        assert "Unknown resume evidence id" in str(exc)
    else:
        raise AssertionError("Expected KeyError for unknown resume evidence id.")


def test_inspect_resume_evidence_cli_json() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/inspect_resume_evidence.py",
            "--bullet",
            "evaluation",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["count"] == 1
    assert payload["entries"][0]["evidence_id"] == "evaluation"
