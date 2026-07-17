from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_script():
    script_path = Path("scripts/run_golden_demo.py")
    spec = importlib.util.spec_from_file_location("run_golden_demo", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_golden_demo_uses_three_public_primary_sources() -> None:
    module = _load_script()

    assert len(module.GOLDEN_SOURCES) == 3
    assert all(url.startswith("https://") for url in module.GOLDEN_SOURCES)
    assert "nist.gov" in module.GOLDEN_SOURCES[0]
    assert "owasp.org" in module.GOLDEN_SOURCES[1]
    assert "arxiv.org" in module.GOLDEN_SOURCES[2]


def test_golden_summary_makes_mock_generation_boundary_explicit() -> None:
    module = _load_script()
    payload = {
        "generated_at_utc": "2026-07-17T00:00:00+00:00",
        "run_id": "run_test",
        "status": "PASS",
        "generation_backend": "mock",
        "embedding_model": "text-embedding-v4",
        "public_source_hosts": ["arxiv.org", "genai.owasp.org", "www.nist.gov"],
        "checks": {
            "real_embedding_configured": {
                "passed": True,
                "observed": "openai-compatible",
            }
        },
    }

    markdown = module._render_summary(payload)

    assert "real-source and real-embedding" in markdown
    assert "must not be described as real-LLM generation" in markdown
