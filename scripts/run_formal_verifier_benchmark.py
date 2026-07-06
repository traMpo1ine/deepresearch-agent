from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.evaluation.llm_verifier_smoke import (  # noqa: E402
    VerifierSmokeConfig,
    run_llm_verifier_smoke,
)
from deepresearch_agent.evaluation.verifier_benchmark import (  # noqa: E402
    aggregate_verifier_runs,
    write_benchmark_outputs,
)


async def run_benchmark(args: argparse.Namespace) -> dict:
    output_dir = Path(args.output_dir) if args.output_dir else _default_output_dir()
    repetitions_dir = output_dir / "repetitions"
    payloads = []
    latencies = []
    for index in range(1, args.repetitions + 1):
        started = time.perf_counter()
        payload = await run_llm_verifier_smoke(
            VerifierSmokeConfig(
                cases_path=Path(args.cases_path),
                output_path=repetitions_dir / f"run_{index:02d}.md",
                output_json_path=repetitions_dir / f"run_{index:02d}.json",
                backend=args.backend,
                model=args.model,
                run_real=args.run_real,
                limit=args.limit,
                max_tokens=args.max_tokens,
            )
        )
        payloads.append(payload)
        latencies.append(time.perf_counter() - started)
    aggregate = aggregate_verifier_runs(payloads, latencies)
    aggregate["protocol"]["cases_path"] = args.cases_path
    aggregate["protocol"]["output_dir"] = str(output_dir)
    write_benchmark_outputs(aggregate, output_dir)
    return aggregate


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a repeated formal verifier benchmark.")
    parser.add_argument("--cases-path", default="data/examples/llm_verifier_cases_extended.jsonl")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--backend", choices=["deepseek", "openai", "vllm", "mock"], default="deepseek")
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--run-real", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.repetitions < 1:
        raise SystemExit("--repetitions must be >= 1")
    payload = asyncio.run(run_benchmark(args))
    if args.json:
        print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    else:
        print(f"Formal verifier benchmark written: {payload['protocol']['output_dir']}")
        print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("reports") / "verifier_benchmark" / f"formal_{stamp}"


if __name__ == "__main__":
    main()
