import json

import pytest

from deepresearch_agent.corpus_profiles import (
    build_profile,
    get_corpus_profile,
    list_corpus_profiles,
)


def test_list_corpus_profiles_contains_resume_ready_profiles() -> None:
    keys = {profile.key for profile in list_corpus_profiles()}

    assert keys >= {
        "offline_agent_docs",
        "resume_agent_docs",
        "paper_reading_docs",
        "local_kb_docs",
    }


def test_build_profile_writes_searcher_compatible_jsonl(tmp_path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "agent.md").write_text(
        "# Agent KB\n\nDeepResearch keeps citation quotes for verifier and repair traces.",
        encoding="utf-8",
    )
    profile = get_corpus_profile("resume_agent_docs")
    local_profile = type(profile)(
        key=profile.key,
        name=profile.name,
        description=profile.description,
        source_dir=source_dir,
        output_path=tmp_path / "resume_agent_docs.jsonl",
    )

    output = build_profile(local_profile)
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]

    assert rows
    assert rows[0]["source_type"] == "corpus_profile"
    assert rows[0]["source_format"] == "md"
    assert rows[0]["profile"] == "resume_agent_docs"
    assert "citation" in rows[0]["topics"]
    assert rows[0]["url"].startswith("profile://resume_agent_docs/")


def test_build_profile_reads_pdf_sources(tmp_path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "kb.pdf").write_bytes(
        b"%PDF-1.4\n"
        b"1 0 obj <<>> endobj\n"
        b"2 0 obj << /Length 58 >> stream\n"
        b"BT /F1 12 Tf 72 720 Td (DeepResearch PDF knowledge base citation) Tj ET\n"
        b"endstream endobj\n"
        b"%%EOF\n"
    )
    profile = get_corpus_profile("local_kb_docs")
    local_profile = type(profile)(
        key=profile.key,
        name=profile.name,
        description=profile.description,
        source_dir=source_dir,
        output_path=tmp_path / "local_kb_docs.jsonl",
    )

    output = build_profile(local_profile)
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]

    assert rows
    assert rows[0]["source_format"] == "pdf"
    assert rows[0]["profile"] == "local_kb_docs"
    assert "DeepResearch PDF knowledge base citation" in rows[0]["text"]


def test_unknown_profile_has_clear_error() -> None:
    with pytest.raises(KeyError, match="Unknown corpus profile"):
        get_corpus_profile("missing")
