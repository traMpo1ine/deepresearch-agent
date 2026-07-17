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
    use_iterative_search: bool,
    max_follow_up_queries: int,
    source_quality_threshold: float,
    enable_web_search: bool,
    web_search_provider: str,
    max_web_results: int,
    embedding_provider: str,
    embedding_base_url: str,
    embedding_model: str,
    embedding_api_key_env: str,
    embedding_cache_path: str | None,
    embedding_timeout_seconds: float,
    embedding_max_retries: int,
    embedding_batch_size: int,
    writer_mode: str,
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
        use_iterative_search=use_iterative_search,
        max_follow_up_queries=max_follow_up_queries,
        source_quality_threshold=source_quality_threshold,
        enable_web_search=enable_web_search,
        web_search_provider=web_search_provider,
        max_web_results=max_web_results,
        embedding_provider=embedding_provider,
        embedding_base_url=embedding_base_url,
        embedding_model=embedding_model,
        embedding_api_key_env=embedding_api_key_env,
        embedding_cache_path=embedding_cache_path,
        embedding_timeout_seconds=embedding_timeout_seconds,
        embedding_max_retries=embedding_max_retries,
        embedding_batch_size=embedding_batch_size,
        writer_mode=writer_mode,
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
    parser.add_argument("--use-iterative-search", action="store_true")
    parser.add_argument("--max-follow-up-queries", type=int, default=1)
    parser.add_argument("--source-quality-threshold", type=float, default=0.58)
    parser.add_argument("--enable-web-search", action="store_true")
    parser.add_argument(
        "--web-search-provider",
        default="disabled",
        help="Comma-separated providers: tavily,wikipedia,searxng.",
    )
    parser.add_argument("--max-web-results", type=int, default=3)
    parser.add_argument(
        "--embedding-provider",
        choices=["hashing", "openai-compatible"],
        default="hashing",
    )
    parser.add_argument(
        "--embedding-base-url",
        default="https://api.openai.com/v1",
    )
    parser.add_argument("--embedding-model", default="text-embedding-3-small")
    parser.add_argument("--embedding-api-key-env", default="EMBEDDING_API_KEY")
    parser.add_argument("--embedding-cache-path")
    parser.add_argument("--embedding-timeout-seconds", type=float, default=30.0)
    parser.add_argument("--embedding-max-retries", type=int, default=2)
    parser.add_argument("--embedding-batch-size", type=int, default=64)
    parser.add_argument(
        "--writer-mode",
        choices=["template", "extractive", "llm"],
        default="template",
    )
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
            args.use_iterative_search,
            args.max_follow_up_queries,
            args.source_quality_threshold,
            args.enable_web_search,
            args.web_search_provider,
            args.max_web_results,
            args.embedding_provider,
            args.embedding_base_url,
            args.embedding_model,
            args.embedding_api_key_env,
            args.embedding_cache_path,
            args.embedding_timeout_seconds,
            args.embedding_max_retries,
            args.embedding_batch_size,
            args.writer_mode,
        )
    )


if __name__ == "__main__":
    main()
