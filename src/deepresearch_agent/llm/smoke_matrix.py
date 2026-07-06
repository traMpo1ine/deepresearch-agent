from __future__ import annotations

import time
from typing import Any

from deepresearch_agent.llm import (
    LLMBackendConfig,
    LLMMessage,
    backend_status,
    create_llm_backend,
)


def default_smoke_configs(vllm_base_url: str = "http://localhost:8000/v1") -> list[LLMBackendConfig]:
    return [
        LLMBackendConfig(backend="mock"),
        LLMBackendConfig(backend="openai"),
        LLMBackendConfig(backend="deepseek"),
        LLMBackendConfig(backend="vllm", vllm_base_url=vllm_base_url),
    ]


async def run_backend_smoke_matrix(
    configs: list[LLMBackendConfig] | None = None,
    run_real: bool = False,
) -> dict[str, Any]:
    rows = []
    for config in configs or default_smoke_configs():
        status = backend_status(config)
        row: dict[str, Any] = {
            **status,
            "smoke_attempted": False,
            "success": False,
            "latency_seconds": 0.0,
            "token_usage": {},
            "cost_estimate": 0.0,
            "error": None,
        }
        should_smoke = config.backend == "mock" or (run_real and status["env_configured"])
        if should_smoke:
            row["smoke_attempted"] = True
            started = time.perf_counter()
            try:
                backend = create_llm_backend(config)
                await backend.complete([LLMMessage(role="user", content="Reply with ok.")])
                row["success"] = True
                row["latency_seconds"] = time.perf_counter() - started
                usage = getattr(backend, "last_usage", {})
                row["token_usage"] = usage
                row["cost_estimate"] = float(usage.get("cost_estimate", 0.0) or 0.0)
            except Exception as exc:  # noqa: BLE001 - smoke matrix should report provider errors.
                row["latency_seconds"] = time.perf_counter() - started
                row["error"] = str(exc)
        rows.append(row)
    return {
        "run_real": run_real,
        "rows": rows,
        "success_count": sum(1 for row in rows if row["success"]),
        "attempted_count": sum(1 for row in rows if row["smoke_attempted"]),
    }


def smoke_matrix_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# LLM Backend Smoke Matrix",
        "",
        f"Run real backends: `{payload['run_real']}`",
        f"Attempted: `{payload['attempted_count']}`",
        f"Successful: `{payload['success_count']}`",
        "",
        "| backend | model | env | attempted | success | latency | cost | error |",
        "|---|---|---|---|---|---:|---:|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['backend']} | {row['model']} | {row['env_configured']} | "
            f"{row['smoke_attempted']} | {row['success']} | "
            f"{row['latency_seconds']:.3f} | {row['cost_estimate']:.4f} | "
            f"{row['error'] or ''} |"
        )
    lines.extend(
        [
            "",
            "Real backend smoke results are configuration checks and should not be mixed with offline/mock ResearchBench metrics.",
        ]
    )
    return "\n".join(lines)
