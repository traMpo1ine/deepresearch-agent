from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.showcase import build_showcase  # noqa: E402


async def run(
    question: str,
    output_dir: str | None,
    planner_mode: str,
    max_concurrency: int,
    repair_rounds: int,
    llm_backend: str,
    model: str | None,
    timeout_seconds: float,
    max_retries: int,
    vllm_base_url: str,
    corpus_path: str,
) -> None:
    result = await build_showcase(
        question=question,
        output_dir=output_dir,
        planner_mode=planner_mode,
        max_concurrency=max_concurrency,
        repair_rounds=repair_rounds,
        llm_backend=llm_backend,
        model=model,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        vllm_base_url=vllm_base_url,
        corpus_path=corpus_path,
    )
    print(f"Showcase generated: {result.output_dir}")
    print(f"Run id: {result.run_id}")
    print(f"Index: {result.files['index_md']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a DeepResearch showcase artifact pack.")
    parser.add_argument("question", help="Research question to showcase.")
    parser.add_argument("--output-dir", help="Output directory. Defaults to reports/showcase/<timestamp>.")
    parser.add_argument("--planner-mode", choices=["template", "heuristic"], default="heuristic")
    parser.add_argument("--max-concurrency", type=int, default=4)
    parser.add_argument("--repair-rounds", type=int, default=2)
    parser.add_argument("--llm-backend", choices=["mock", "openai", "deepseek", "vllm"], default="mock")
    parser.add_argument("--model")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--vllm-base-url", default="http://localhost:8000/v1")
    parser.add_argument("--corpus-path", default="data/corpus/offline_corpus.jsonl")
    args = parser.parse_args()
    asyncio.run(
        run(
            args.question,
            args.output_dir,
            args.planner_mode,
            args.max_concurrency,
            args.repair_rounds,
            args.llm_backend,
            args.model,
            args.timeout_seconds,
            args.max_retries,
            args.vllm_base_url,
            args.corpus_path,
        )
    )


if __name__ == "__main__":
    main()
