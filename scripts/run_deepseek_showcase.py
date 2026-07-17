from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
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


DEFAULT_QUESTION = "为什么 DeepResearch Agent 需要引用验证和 Red-Blue 修复？"
ALLOWED_ENV_KEYS = {"DEEPSEEK_API_KEY"}


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if name in ALLOWED_ENV_KEYS:
            os.environ.setdefault(name, value.strip())


async def run(
    question: str,
    model: str,
    max_tokens: int,
    run_real: bool,
    output: str | None,
    as_json: bool,
) -> None:
    config = LLMBackendConfig(
        backend="deepseek",
        model=model,
        timeout_seconds=60.0,
        max_retries=1,
        max_tokens=max_tokens,
    )
    status = backend_status(config)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "question": question,
        "backend_status": status,
        "run_real": run_real,
        "success": False,
        "answer_preview": "",
        "answer": "",
        "token_usage": {},
        "error": None,
        "boundary": (
            "This is a real DeepSeek API showcase only. It is not mixed into offline/mock "
            "ResearchBench metrics."
        ),
    }
    if not run_real:
        payload["error"] = "Dry run only. Pass --run-real after setting DEEPSEEK_API_KEY."
    elif not status["env_configured"]:
        payload["error"] = "DEEPSEEK_API_KEY is not configured."
    else:
        try:
            backend = create_llm_backend(config)
            answer = await backend.complete(_messages(question))
            payload["success"] = True
            payload["answer"] = answer
            payload["answer_preview"] = answer[:500]
            payload["token_usage"] = getattr(backend, "last_usage", {})
        except Exception as exc:  # noqa: BLE001 - showcase should capture provider errors.
            payload["error"] = str(exc)

    text = json.dumps(payload, ensure_ascii=False, indent=2) if as_json else _markdown(payload)
    output_path = Path(output) if output else Path("reports") / "real_api" / "deepseek_showcase.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    print(text)
    print(f"\nSaved to: {output_path}")


def _messages(question: str) -> list[LLMMessage]:
    return [
        LLMMessage(
            role="system",
            content=(
                "You are the Writer in a grounded DeepResearch system. "
                "Answer concisely in Chinese and do not invent benchmark numbers."
            ),
        ),
        LLMMessage(
            role="user",
            content=(
                f"问题：{question}\n\n"
                "请用 4 点说明引用验证和修复对研究系统可靠性的作用，"
                "并指出 2 个仍需继续优化的工程边界。"
            ),
        ),
    ]


def _markdown(payload: dict) -> str:
    status = payload["backend_status"]
    usage = payload.get("token_usage", {})
    lines = [
        "# DeepSeek Real API Showcase",
        "",
        f"Generated at: `{payload['generated_at']}`",
        f"Question: {payload['question']}",
        "",
        "## Backend",
        "",
        f"- backend: `{status['backend']}`",
        f"- model: `{status['model']}`",
        f"- base_url: `{status['base_url']}`",
        f"- max_tokens: `{status['max_tokens']}`",
        f"- env_configured: `{str(status['env_configured']).lower()}`",
        f"- run_real: `{str(payload['run_real']).lower()}`",
        "",
        "## Result",
        "",
        f"- success: `{str(payload['success']).lower()}`",
        f"- error: `{payload['error'] or ''}`",
        f"- prompt_tokens: `{usage.get('prompt_tokens', 0)}`",
        f"- completion_tokens: `{usage.get('completion_tokens', 0)}`",
        f"- total_tokens: `{usage.get('total_tokens', 0)}`",
        f"- estimated_cost_usd: `{float(usage.get('cost_estimate_usd', 0.0) or 0.0):.8f}`",
        f"- pricing_source: `{usage.get('pricing_source', '')}`",
        "",
        "## Answer",
        "",
        payload["answer"] or "No real answer was generated.",
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a bounded low-cost DeepSeek real API showcase.")
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--run-real", action="store_true", help="Call DeepSeek when DEEPSEEK_API_KEY is set.")
    parser.add_argument("--output")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--json", action="store_true", help="Write JSON instead of Markdown.")
    args = parser.parse_args()
    _load_env_file(Path(args.env_file))
    asyncio.run(
        run(
            question=args.question,
            model=args.model,
            max_tokens=args.max_tokens,
            run_real=args.run_real,
            output=args.output,
            as_json=args.json,
        )
    )


if __name__ == "__main__":
    main()
