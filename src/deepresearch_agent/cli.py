from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from deepresearch_agent.config import config_get, load_config
from deepresearch_agent.orchestration.coordinator import ResearchCoordinator


async def run(
    question: str,
    memory_path: str = "data/memory/deepresearch.sqlite3",
    vector_path: str = "data/memory/vector_index.npz",
    plan_dir: str = "reports/plans",
    output: str | None = None,
    output_json: str | None = None,
    llm_backend: str = "mock",
    model: str | None = None,
    max_repair_rounds: int = 2,
    timeout_seconds: float = 60.0,
    max_retries: int = 2,
    vllm_base_url: str = "http://localhost:8000/v1",
    max_concurrency: int = 4,
    planner_mode: str = "heuristic",
    corpus_path: str = "data/corpus/offline_corpus.jsonl",
) -> None:
    coordinator = ResearchCoordinator(
        max_concurrency=max_concurrency,
        memory_path=memory_path,
        vector_path=vector_path,
        plan_dir=plan_dir,
        llm_backend=llm_backend,
        model=model,
        repair_rounds=max_repair_rounds,
        llm_timeout_seconds=timeout_seconds,
        llm_max_retries=max_retries,
        llm_vllm_base_url=vllm_base_url,
        planner_mode=planner_mode,
        corpus_path=corpus_path,
    )
    report = await coordinator.run(question)
    markdown = report.to_markdown()
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
    if output_json:
        path = Path(output_json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report.to_json(), encoding="utf-8")
    print(markdown)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the DeepResearch Agent pipeline.")
    parser.add_argument("question", help="Research question to investigate.")
    parser.add_argument("--config", default="configs/default.toml")
    parser.add_argument("--memory-path", default=None)
    parser.add_argument("--vector-path", default=None)
    parser.add_argument("--plan-dir", default=None)
    parser.add_argument("--output", help="Optional Markdown output path.")
    parser.add_argument("--output-json", help="Optional JSON output path.")
    parser.add_argument("--llm-backend", default=None, choices=["mock", "deepseek", "openai", "vllm"])
    parser.add_argument("--model", default=None)
    parser.add_argument("--max-repair-rounds", type=int, default=None)
    parser.add_argument("--timeout-seconds", type=float, default=None)
    parser.add_argument("--max-retries", type=int, default=None)
    parser.add_argument("--vllm-base-url", default=None)
    parser.add_argument("--max-concurrency", type=int, default=None)
    parser.add_argument("--planner-mode", choices=["template", "heuristic"], default=None)
    parser.add_argument("--corpus-path", default=None)
    args = parser.parse_args()
    config = load_config(args.config)
    asyncio.run(
        run(
            args.question,
            args.memory_path or config_get(config, "memory.sqlite_path", "data/memory/deepresearch.sqlite3"),
            args.vector_path or config_get(config, "memory.vector_path", "data/memory/vector_index.npz"),
            args.plan_dir or config_get(config, "pipeline.plan_dir", "reports/plans"),
            args.output,
            args.output_json,
            args.llm_backend or config_get(config, "llm.backend", "mock"),
            args.model or config_get(config, "llm.model", None),
            args.max_repair_rounds
            if args.max_repair_rounds is not None
            else config_get(config, "pipeline.repair_rounds", 2),
            args.timeout_seconds
            if args.timeout_seconds is not None
            else config_get(config, "runtime.task_timeout_seconds", 60.0),
            args.max_retries if args.max_retries is not None else 2,
            args.vllm_base_url or config_get(config, "llm.vllm_base_url", "http://localhost:8000/v1"),
            args.max_concurrency
            if args.max_concurrency is not None
            else config_get(config, "runtime.max_concurrency", 4),
            args.planner_mode or config_get(config, "pipeline.planner_mode", "heuristic"),
            args.corpus_path or config_get(config, "pipeline.corpus_path", "data/corpus/offline_corpus.jsonl"),
        )
    )
