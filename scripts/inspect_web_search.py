from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.tools.web_search import (  # noqa: E402
    create_web_search_provider,
    web_search_status,
)


async def run(
    query: str,
    provider_name: str,
    max_results: int,
    cache_path: str | None,
    cache_ttl_seconds: int,
    cache_backend: str,
    redis_url: str | None,
) -> None:
    provider = create_web_search_provider(
        provider_name,
        cache_path=cache_path,
        cache_ttl_seconds=cache_ttl_seconds,
        cache_backend=cache_backend,
        redis_url=redis_url,
    )
    results = await provider.search(query, max_results=max_results)
    payload = {
        "query": query,
        "status": web_search_status(provider_name),
        "result_count": len(results),
        "results": [asdict(item) for item in results],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect real web-source retrieval without an LLM.")
    parser.add_argument("query")
    parser.add_argument("--provider", default="wikipedia")
    parser.add_argument("--max-results", type=int, default=3)
    parser.add_argument("--cache-path", default="data/memory/web_search_cache.sqlite3")
    parser.add_argument("--cache-ttl-seconds", type=int, default=3600)
    parser.add_argument("--cache-backend", choices=["sqlite", "redis"], default="sqlite")
    parser.add_argument("--redis-url")
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()
    asyncio.run(
        run(
            args.query,
            args.provider,
            args.max_results,
            None if args.no_cache else args.cache_path,
            args.cache_ttl_seconds,
            args.cache_backend,
            args.redis_url,
        )
    )


if __name__ == "__main__":
    main()
