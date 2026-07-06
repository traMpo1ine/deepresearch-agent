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

from deepresearch_agent.evaluation.llm_verifier_smoke import (  # noqa: E402
    VerifierSmokeConfig,
    run_llm_verifier_smoke,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run optional LLM verifier smoke cases.")
    parser.add_argument("--cases-path", default="data/examples/llm_verifier_cases.jsonl")
    parser.add_argument("--output", default="reports/llm_verifier_smoke.md")
    parser.add_argument("--output-json", default=None)
    parser.add_argument("--backend", choices=["deepseek", "openai", "vllm", "mock"], default="deepseek")
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--run-real", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = asyncio.run(
        run_llm_verifier_smoke(
            VerifierSmokeConfig(
                cases_path=Path(args.cases_path),
                output_path=Path(args.output),
                output_json_path=Path(args.output_json) if args.output_json else None,
                backend=args.backend,
                model=args.model,
                run_real=args.run_real,
                limit=args.limit,
                max_tokens=args.max_tokens,
            )
        )
    )
    if args.json:
        print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    else:
        print(f"LLM verifier smoke written: {args.output}")
        print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
