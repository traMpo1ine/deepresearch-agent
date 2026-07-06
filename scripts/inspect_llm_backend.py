from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.llm import (  # noqa: E402
    LLMBackendConfig,
    LLMMessage,
    backend_status,
    create_llm_backend,
)
from deepresearch_agent.schemas.serialization import dumps_json  # noqa: E402


async def run(
    backend: str,
    model: str | None,
    timeout_seconds: float,
    max_retries: int,
    vllm_base_url: str,
    max_tokens: int | None,
    smoke: bool,
    as_json: bool,
) -> None:
    config = LLMBackendConfig(
        backend=backend,  # type: ignore[arg-type]
        model=model,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        vllm_base_url=vllm_base_url,
        max_tokens=max_tokens,
    )
    status = backend_status(config)
    payload = {"status": status, "smoke": None}
    if smoke:
        llm = create_llm_backend(config)
        text = await llm.complete([LLMMessage(role="user", content="Reply with ok.")])
        payload["smoke"] = {
            "completion_preview": text[:120],
            "token_usage": getattr(llm, "last_usage", {}),
        }
    if as_json:
        print(dumps_json(payload))
    else:
        print(_payload_to_markdown(payload))


def _payload_to_markdown(payload: dict) -> str:
    status = payload["status"]
    lines = [
        "# LLM Backend Inspection",
        "",
        f"Backend: `{status['backend']}`",
        f"Model: `{status['model']}`",
        f"Base URL: `{status['base_url']}`",
        f"Timeout seconds: `{status['timeout_seconds']}`",
        f"Max retries: `{status['max_retries']}`",
        f"Max tokens: `{status['max_tokens']}`",
        f"Env var: `{status['env_var']}`",
        f"Env configured: `{str(status['env_configured']).lower()}`",
        f"Offline safe: `{str(status['offline_safe']).lower()}`",
        "",
    ]
    if payload["smoke"]:
        lines.extend(
            [
                "## Smoke Result",
                "",
                f"Completion preview: {payload['smoke']['completion_preview']}",
                f"Token usage: `{payload['smoke']['token_usage']}`",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "Smoke was not executed. Use `--smoke` only when the selected backend is configured.",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect configured LLM backend without running research.")
    parser.add_argument("--backend", choices=["mock", "openai", "deepseek", "vllm"], default="mock")
    parser.add_argument("--model")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--vllm-base-url", default="http://localhost:8000/v1")
    parser.add_argument("--max-tokens", type=int)
    parser.add_argument("--smoke", action="store_true", help="Run a real chat completion smoke test.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    args = parser.parse_args()
    asyncio.run(
        run(
            args.backend,
            args.model,
            args.timeout_seconds,
            args.max_retries,
            args.vllm_base_url,
            args.max_tokens,
            args.smoke,
            args.json,
        )
    )


if __name__ == "__main__":
    main()
