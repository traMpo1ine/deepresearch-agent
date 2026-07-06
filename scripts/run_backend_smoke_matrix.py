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

from deepresearch_agent.llm.smoke_matrix import (  # noqa: E402
    default_smoke_configs,
    run_backend_smoke_matrix,
    smoke_matrix_markdown,
)


async def run(run_real: bool, vllm_base_url: str, output: str | None, as_json: bool) -> None:
    payload = await run_backend_smoke_matrix(
        default_smoke_configs(vllm_base_url=vllm_base_url),
        run_real=run_real,
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2) if as_json else smoke_matrix_markdown(payload)
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    print(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM backend dry-run/smoke matrix.")
    parser.add_argument("--run-real", action="store_true", help="Attempt real providers when env vars exist.")
    parser.add_argument("--vllm-base-url", default="http://localhost:8000/v1")
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    args = parser.parse_args()
    asyncio.run(run(args.run_real, args.vllm_base_url, args.output, args.json))


if __name__ == "__main__":
    main()
