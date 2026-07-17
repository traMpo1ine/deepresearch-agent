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
    use_iterative_search: bool = False,
    max_follow_up_queries: int = 1,
    source_quality_threshold: float = 0.58,
    enable_web_search: bool = False,
    web_search_provider: str = "disabled",
    max_web_results: int = 3,
    web_search_cache_path: str | None = "data/memory/web_search_cache.sqlite3",
    web_search_cache_ttl_seconds: int = 3600,
    web_search_cache_backend: str = "sqlite",
    web_search_redis_url: str | None = None,
    embedding_provider: str = "hashing",
    embedding_base_url: str = "https://api.openai.com/v1",
    embedding_model: str = "text-embedding-3-small",
    embedding_api_key_env: str = "EMBEDDING_API_KEY",
    embedding_cache_path: str = "data/memory/embedding_cache.sqlite3",
    embedding_timeout_seconds: float = 30.0,
    embedding_max_retries: int = 2,
    embedding_batch_size: int = 64,
    writer_mode: str = "template",
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
        use_iterative_search=use_iterative_search,
        max_follow_up_queries=max_follow_up_queries,
        source_quality_threshold=source_quality_threshold,
        enable_web_search=enable_web_search,
        web_search_provider=web_search_provider,
        max_web_results=max_web_results,
        web_search_cache_path=web_search_cache_path,
        web_search_cache_ttl_seconds=web_search_cache_ttl_seconds,
        web_search_cache_backend=web_search_cache_backend,
        web_search_redis_url=web_search_redis_url,
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
    parser.add_argument("--use-iterative-search", action="store_true")
    parser.add_argument("--max-follow-up-queries", type=int, default=None)
    parser.add_argument("--source-quality-threshold", type=float, default=None)
    parser.add_argument("--enable-web-search", action="store_true")
    parser.add_argument(
        "--web-search-provider",
        default=None,
        help="Comma-separated providers: tavily,wikipedia,searxng.",
    )
    parser.add_argument("--max-web-results", type=int, default=None)
    parser.add_argument("--web-search-cache-path", default=None)
    parser.add_argument("--web-search-cache-ttl-seconds", type=int, default=None)
    parser.add_argument("--web-search-cache-backend", choices=["sqlite", "redis"], default=None)
    parser.add_argument("--web-search-redis-url", default=None)
    parser.add_argument(
        "--embedding-provider",
        choices=["hashing", "openai-compatible"],
        default=None,
    )
    parser.add_argument("--embedding-base-url", default=None)
    parser.add_argument("--embedding-model", default=None)
    parser.add_argument("--embedding-api-key-env", default=None)
    parser.add_argument("--embedding-cache-path", default=None)
    parser.add_argument("--embedding-timeout-seconds", type=float, default=None)
    parser.add_argument("--embedding-max-retries", type=int, default=None)
    parser.add_argument("--embedding-batch-size", type=int, default=None)
    parser.add_argument("--writer-mode", choices=["template", "extractive", "llm"], default=None)
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
            args.use_iterative_search or bool(config_get(config, "pipeline.use_iterative_search", False)),
            args.max_follow_up_queries
            if args.max_follow_up_queries is not None
            else int(config_get(config, "pipeline.max_follow_up_queries", 1)),
            args.source_quality_threshold
            if args.source_quality_threshold is not None
            else float(config_get(config, "pipeline.source_quality_threshold", 0.58)),
            args.enable_web_search or bool(config_get(config, "pipeline.enable_web_search", False)),
            args.web_search_provider or config_get(config, "pipeline.web_search_provider", "disabled"),
            args.max_web_results
            if args.max_web_results is not None
            else int(config_get(config, "pipeline.max_web_results", 3)),
            args.web_search_cache_path
            or config_get(
                config,
                "pipeline.web_search_cache_path",
                "data/memory/web_search_cache.sqlite3",
            ),
            args.web_search_cache_ttl_seconds
            if args.web_search_cache_ttl_seconds is not None
            else int(config_get(config, "pipeline.web_search_cache_ttl_seconds", 3600)),
            args.web_search_cache_backend
            or config_get(config, "pipeline.web_search_cache_backend", "sqlite"),
            args.web_search_redis_url
            or config_get(config, "pipeline.web_search_redis_url", None),
            args.embedding_provider
            or config_get(config, "pipeline.embedding_provider", "hashing"),
            args.embedding_base_url
            or config_get(
                config,
                "pipeline.embedding_base_url",
                "https://api.openai.com/v1",
            ),
            args.embedding_model
            or config_get(config, "pipeline.embedding_model", "text-embedding-3-small"),
            args.embedding_api_key_env
            or config_get(config, "pipeline.embedding_api_key_env", "EMBEDDING_API_KEY"),
            args.embedding_cache_path
            or config_get(
                config,
                "pipeline.embedding_cache_path",
                "data/memory/embedding_cache.sqlite3",
            ),
            args.embedding_timeout_seconds
            if args.embedding_timeout_seconds is not None
            else float(config_get(config, "pipeline.embedding_timeout_seconds", 30.0)),
            args.embedding_max_retries
            if args.embedding_max_retries is not None
            else int(config_get(config, "pipeline.embedding_max_retries", 2)),
            args.embedding_batch_size
            if args.embedding_batch_size is not None
            else int(config_get(config, "pipeline.embedding_batch_size", 64)),
            args.writer_mode or config_get(config, "pipeline.writer_mode", "template"),
        )
    )
