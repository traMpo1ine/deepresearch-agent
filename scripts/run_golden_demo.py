from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.showcase import build_showcase  # noqa: E402


GOLDEN_SOURCES = (
    "https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence",
    "https://genai.owasp.org/llm-top-10/",
    "https://arxiv.org/abs/2405.07437",
)

GOLDEN_QUESTION = (
    "请基于下面三份公开资料，为一个可审计的 DeepResearch Agent 设计工程方案："
    "说明为什么要分别评测检索与生成、如何保留引用溯源，以及如何把提示注入作为不可信输入处理。"
    "请区分资料明确支持的结论与工程推断，并给出可以落地的最小检查清单。\n"
    + "\n".join(GOLDEN_SOURCES)
)

ALLOWED_ENV_KEYS = {
    "EMBEDDING_API_KEY",
    "EMBEDDING_BASE_URL",
    "EMBEDDING_MODEL",
    "DEEPSEEK_API_KEY",
}


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


def _source_hosts(report: dict[str, object]) -> list[str]:
    evidence = report.get("evidence", [])
    hosts = {
        urlparse(str(item.get("url", ""))).netloc.lower()
        for item in evidence
        if isinstance(item, dict) and str(item.get("url", "")).startswith("http")
    }
    return sorted(host for host in hosts if host)


def _render_summary(payload: dict[str, object]) -> str:
    checks = payload["checks"]
    writer_generation = payload.get("writer_generation", {})
    llm_usage = payload.get("llm_usage", {})
    lines = [
        "# Golden DeepResearch Demo",
        "",
        f"- Generated (UTC): `{payload['generated_at_utc']}`",
        f"- Run id: `{payload['run_id']}`",
        f"- Overall status: **{payload['status']}**",
        f"- Generation backend: `{payload['generation_backend']}`",
        f"- Embedding model: `{payload['embedding_model']}`",
        f"- Public source hosts: `{', '.join(payload['public_source_hosts'])}`",
        f"- Writer mode: `{writer_generation.get('mode', 'unknown')}`",
        f"- Writer fallback: `{writer_generation.get('fallback', 'unknown')}`",
        f"- LLM tokens: `{llm_usage.get('total_tokens', 0)}`",
        f"- Estimated LLM cost (USD): `{float(llm_usage.get('cost_estimate_usd', 0.0) or 0.0):.8f}`",
        "",
        "## Acceptance checks",
        "",
        "| Check | Passed | Observed |",
        "|---|---|---|",
    ]
    for name, check in checks.items():
        lines.append(f"| {name} | {check['passed']} | {check['observed']} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            (
                (
                    "This pack proves a controlled real-source, real-embedding, and DeepSeek Writer "
                    "execution. The Writer acceptance check fails if the model returns no valid cited "
                    "claims and the system falls back to extractive generation."
                    if payload["generation_backend"] == "deepseek"
                    else "This pack proves a controlled real-source and real-embedding execution. "
                    "When `generation_backend=mock`, the Writer/Verifier/Red-Blue path is deterministic "
                    "and must not be described as real-LLM generation. Run again with "
                    "`--llm-backend deepseek` only after configuring `DEEPSEEK_API_KEY`."
                )
            ),
            "",
            "## Reproduce",
            "",
            "```powershell",
            (
                "uv run python scripts/run_golden_demo.py --llm-backend deepseek"
                if payload["generation_backend"] == "deepseek"
                else "uv run python scripts/run_golden_demo.py"
            ),
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


async def _run(args: argparse.Namespace) -> int:
    _load_env_file(Path(args.env_file))
    if not os.getenv("EMBEDDING_API_KEY"):
        raise SystemExit("EMBEDDING_API_KEY is missing; configure it in .env first.")
    if args.llm_backend == "deepseek" and not os.getenv("DEEPSEEK_API_KEY"):
        raise SystemExit("DEEPSEEK_API_KEY is required for --llm-backend deepseek.")

    output_dir = Path(args.output_dir)
    result = await build_showcase(
        question=GOLDEN_QUESTION,
        output_dir=output_dir,
        planner_mode="heuristic",
        max_concurrency=3,
        repair_rounds=2,
        llm_backend=args.llm_backend,
        model=args.model,
        timeout_seconds=60.0,
        max_retries=2,
        corpus_path="data/corpus/offline_corpus.jsonl",
        use_iterative_search=False,
        enable_web_search=True,
        web_search_provider="url",
        max_web_results=3,
        embedding_provider="openai-compatible",
        embedding_base_url=os.getenv(
            "EMBEDDING_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ),
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-v4"),
        embedding_cache_path=output_dir / "embedding_cache.sqlite3",
        embedding_timeout_seconds=30.0,
        embedding_max_retries=2,
        embedding_batch_size=64,
        writer_mode="extractive" if args.llm_backend == "mock" else "llm",
    )

    report = json.loads(result.files["report_json"].read_text(encoding="utf-8"))
    run_summary = report["run_summary"]
    embedding = run_summary.get("embedding_telemetry", {})
    live_sources = run_summary.get("live_sources", {})
    writer_generation = run_summary.get("writer_generation", {})
    llm_usage = run_summary.get("llm_usage", {})
    hosts = _source_hosts(report)
    checks = {
        "real_embedding_configured": {
            "passed": embedding.get("provider") == "openai_compatible",
            "observed": embedding.get("provider"),
        },
        "embedding_model_expected": {
            "passed": embedding.get("model") == os.getenv("EMBEDDING_MODEL", "text-embedding-v4"),
            "observed": embedding.get("model"),
        },
        "public_sources_retrieved": {
            "passed": len(hosts) >= 2,
            "observed": len(hosts),
        },
        "source_lineage_complete": {
            "passed": float(live_sources.get("lineage_complete_rate", 0.0)) >= 0.9,
            "observed": live_sources.get("lineage_complete_rate", 0.0),
        },
        "evidence_created": {
            "passed": int(run_summary.get("evidence_count", 0)) >= 3,
            "observed": run_summary.get("evidence_count", 0),
        },
        "claims_created": {
            "passed": len(report.get("claims", [])) >= 1,
            "observed": len(report.get("claims", [])),
        },
        "public_source_cited": {
            "passed": any(
                evidence_id in {
                    item.get("id")
                    for item in report.get("evidence", [])
                    if isinstance(item, dict)
                    and str(item.get("url", "")).startswith(("http://", "https://"))
                }
                for claim in report.get("claims", [])
                if isinstance(claim, dict)
                for evidence_id in claim.get("citation_ids", [])
            ),
            "observed": sum(
                1
                for claim in report.get("claims", [])
                if isinstance(claim, dict)
                and any(
                    evidence_id in {
                        item.get("id")
                        for item in report.get("evidence", [])
                        if isinstance(item, dict)
                        and str(item.get("url", "")).startswith(("http://", "https://"))
                    }
                    for evidence_id in claim.get("citation_ids", [])
                )
            ),
        },
        "verification_trace_created": {
            "passed": any(
                isinstance(claim, dict) and claim.get("verification_trace")
                for claim in report.get("claims", [])
            ),
            "observed": sum(
                1
                for claim in report.get("claims", [])
                if isinstance(claim, dict) and claim.get("verification_trace")
            ),
        },
        "writer_generation_valid": {
            "passed": (
                writer_generation.get("mode") == "llm"
                and writer_generation.get("fallback") is False
                if args.llm_backend == "deepseek"
                else writer_generation.get("mode") == "extractive"
            ),
            "observed": {
                "mode": writer_generation.get("mode"),
                "fallback": writer_generation.get("fallback"),
            },
        },
    }
    status = "PASS" if all(check["passed"] for check in checks.values()) else "FAIL"
    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "run_id": result.run_id,
        "question": GOLDEN_QUESTION,
        "source_urls": list(GOLDEN_SOURCES),
        "public_source_hosts": hosts,
        "generation_backend": args.llm_backend,
        "generation_is_real_llm": args.llm_backend != "mock",
        "embedding_model": embedding.get("model"),
        "embedding_telemetry": embedding,
        "live_source_summary": live_sources,
        "writer_generation": writer_generation,
        "llm_usage": llm_usage,
        "checks": checks,
        "artifacts": {name: path.name for name, path in result.files.items()},
        "interpretation_boundary": (
            "Controlled real-source and real-embedding demo. Mock generation is deterministic "
            "and is not evidence of real-LLM generation quality."
        ),
    }
    (output_dir / "golden_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "golden_summary.md").write_text(_render_summary(payload), encoding="utf-8")
    print(output_dir / "golden_summary.md")
    return 0 if status == "PASS" else 2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the frozen real-source + real-embedding golden DeepResearch demo."
    )
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--output-dir", default="reports/golden_demo/v1")
    parser.add_argument("--llm-backend", choices=["mock", "deepseek"], default="mock")
    parser.add_argument("--model")
    return asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
