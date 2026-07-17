import pytest

from deepresearch_agent.llm import (
    DeepSeekBackend,
    LLMBackendConfig,
    LLMMessage,
    MockLLMBackend,
    backend_status,
    create_llm_backend,
)
from deepresearch_agent.llm.openai_compatible import LLMProviderHTTPError
from deepresearch_agent.orchestration import ResearchCoordinator


@pytest.mark.asyncio
async def test_mock_backend_factory_runs_offline() -> None:
    backend = create_llm_backend(LLMBackendConfig(backend="mock"))

    text = await backend.complete([LLMMessage(role="user", content="hello")])
    embedding = await backend.embed("agent memory citation")

    assert isinstance(backend, MockLLMBackend)
    assert "Mock response" in text
    assert len(embedding) == 64


@pytest.mark.asyncio
async def test_deepseek_structured_completion_requests_json_output(monkeypatch) -> None:
    backend = DeepSeekBackend(max_tokens=256)
    captured_payload = {}

    async def fake_post_json(path, payload):
        captured_payload.update(payload)
        return {
            "choices": [{"message": {"content": '{"claims": []}'}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 4},
        }

    monkeypatch.setattr(backend, "_post_json", fake_post_json)

    result = await backend.structured_complete(
        [LLMMessage(role="user", content="Return JSON with a claims array.")]
    )

    assert result["claims"] == []
    assert captured_payload["response_format"] == {"type": "json_object"}
    assert captured_payload["thinking"] == {"type": "disabled"}


@pytest.mark.asyncio
async def test_deepseek_does_not_retry_non_retryable_provider_error(monkeypatch) -> None:
    backend = DeepSeekBackend(max_retries=2)
    attempts = 0

    def fake_send(request):
        nonlocal attempts
        attempts += 1
        raise LLMProviderHTTPError(400, "invalid request")

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    monkeypatch.setattr(backend, "_send", fake_send)

    with pytest.raises(LLMProviderHTTPError, match="invalid request"):
        await backend.complete([LLMMessage(role="user", content="Hello")])

    assert attempts == 1


def test_backend_status_reports_provider_configuration() -> None:
    status = backend_status(LLMBackendConfig(backend="deepseek"))

    assert status["backend"] == "deepseek"
    assert status["model"] == "deepseek-v4-flash"
    assert status["base_url"] == "https://api.deepseek.com"
    assert status["max_tokens"] == 512
    assert status["env_var"] == "DEEPSEEK_API_KEY"
    assert not status["offline_safe"]


def test_deepseek_backend_estimates_low_cost_usage() -> None:
    backend = DeepSeekBackend(model="deepseek-v4-flash", max_tokens=256)

    backend._record_usage(  # noqa: SLF001 - cost estimation is a local accounting helper.
        {
            "usage": {
                "prompt_tokens": 1000,
                "completion_tokens": 500,
                "total_tokens": 1500,
            }
        },
        latency_seconds=0.1,
    )

    assert backend.last_usage["cost_estimate_usd"] == pytest.approx(0.00028)
    assert backend.last_usage["pricing_source"] == "deepseek_api_docs_2026_07"


def test_vllm_status_uses_configured_base_url() -> None:
    status = backend_status(
        LLMBackendConfig(
            backend="vllm",
            model="qwen-local",
            vllm_base_url="http://127.0.0.1:9000/v1",
        )
    )

    assert status["model"] == "qwen-local"
    assert status["base_url"] == "http://127.0.0.1:9000/v1"


def test_coordinator_constructs_configured_llm_backend(tmp_path) -> None:
    coordinator = ResearchCoordinator(
        memory_path=tmp_path / "memory.sqlite3",
        vector_path=tmp_path / "vector.npz",
        plan_dir=tmp_path / "plans",
        llm_backend="mock",
    )

    assert isinstance(coordinator.llm, MockLLMBackend)


@pytest.mark.asyncio
async def test_coordinator_records_llm_backend_status_in_run_summary(tmp_path) -> None:
    coordinator = ResearchCoordinator(
        memory_path=tmp_path / "memory.sqlite3",
        vector_path=tmp_path / "vector.npz",
        plan_dir=tmp_path / "plans",
        llm_backend="mock",
        model="mock-researcher-v1",
        llm_vllm_base_url="http://127.0.0.1:9000/v1",
    )

    report = await coordinator.run("Why should an offline agent record backend configuration?")

    assert report.run_summary["llm_backend"] == "mock"
    assert report.run_summary["model"] == "mock-researcher-v1"
    assert report.run_summary["llm_vllm_base_url"] == "http://127.0.0.1:9000/v1"
    assert report.run_summary["llm_status"]["backend"] == "mock"
    assert report.run_summary["llm_status"]["offline_safe"] is True
