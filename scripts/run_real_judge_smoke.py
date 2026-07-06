from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.evaluation.real_judge_smoke import (  # noqa: E402
    real_judge_smoke_markdown,
    run_real_judge_smoke,
)
from deepresearch_agent.llm import LLMBackendConfig  # noqa: E402


async def run(
    backend: str,
    model: str | None,
    dataset: str,
    limit: int,
    run_real: bool,
    output: str | None,
    as_json: bool,
) -> None:
    payload = await run_real_judge_smoke(
        LLMBackendConfig(backend=backend, model=model),
        dataset_path=dataset,
        limit=limit,
        run_real=run_real,
    )
    text = (
        json.dumps(payload, ensure_ascii=False, indent=2)
        if as_json
        else real_judge_smoke_markdown(payload)
    )
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    print(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run optional LLM-as-Judge smoke checks.")
    parser.add_argument("--backend", choices=["mock", "openai", "deepseek", "vllm"], default="mock")
    parser.add_argument("--model")
    parser.add_argument("--dataset", default="data/benchmarks/researchbench.jsonl")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--run-real", action="store_true", help="Call real providers when env vars exist.")
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    args = parser.parse_args()
    asyncio.run(
        run(
            args.backend,
            args.model,
            args.dataset,
            args.limit,
            args.run_real,
            args.output,
            args.json,
        )
    )


if __name__ == "__main__":
    main()
