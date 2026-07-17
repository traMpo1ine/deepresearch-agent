from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from deepresearch_agent.agents.searcher import SearcherAgent
from deepresearch_agent.evaluation.retrieval import (
    evaluate_searcher,
    load_retrieval_cases,
    validate_relevance_labels,
)
from deepresearch_agent.memory import OpenAICompatibleEmbeddingProvider


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _metric(summary: dict[str, object], name: str) -> str:
    return f"{float(summary[name]):.3f}"


def _render_markdown(payload: dict[str, object]) -> str:
    ks = payload["ks"]
    max_k = max(ks)
    lines = [
        "# Retrieval Quality Evaluation",
        "",
        f"- Generated (UTC): `{payload['generated_at_utc']}`",
        f"- Benchmark: `{payload['benchmark_path']}`",
        f"- Benchmark SHA-256: `{payload['benchmark_sha256']}`",
        f"- Corpus: `{payload['corpus_path']}`",
        f"- Corpus SHA-256: `{payload['corpus_sha256']}`",
        f"- Cases: **{payload['case_count']}**",
        f"- Cutoffs: `{', '.join(f'K={k}' for k in ks)}`",
        f"- Embedding provider: `{payload['embedding']['provider']}`",
        "",
        "The benchmark uses frozen questions and their `required_sources` labels. Web search is "
        "disabled, so this measures local retrieval only. Check the benchmark documentation before "
        "interpreting a development set as a held-out result.",
        "",
        "## Mode comparison",
        "",
        f"| Mode | Recall@1 | Recall@3 | Recall@{max_k} | Hit@{max_k} | "
        f"All relevant@{max_k} | MRR@{max_k} | nDCG@{max_k} | Failures |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for mode, evaluation in payload["evaluations"].items():
        summary = evaluation["summary"]
        lines.append(
            f"| {mode} | {_metric(summary, 'recall_at_1')} | "
            f"{_metric(summary, 'recall_at_3')} | {_metric(summary, f'recall_at_{max_k}')} | "
            f"{_metric(summary, f'hit_rate_at_{max_k}')} | "
            f"{_metric(summary, f'all_relevant_at_{max_k}')} | "
            f"{_metric(summary, f'mrr_at_{max_k}')} | "
            f"{_metric(summary, f'ndcg_at_{max_k}')} | "
            f"{len(evaluation['failures_at_max_k'])} |"
        )

    lines.extend(["", "## Hybrid breakdown", ""])
    hybrid = payload["evaluations"].get("hybrid")
    if hybrid:
        for field in ("difficulty", "domain", "required_hops", "language", "query_style"):
            lines.extend(
                [
                    f"### By {field}",
                    "",
                    f"| Group | Cases | Recall@{max_k} | All relevant@{max_k} | MRR@{max_k} |",
                    "|---|---:|---:|---:|---:|",
                ]
            )
            for group, summary in hybrid["breakdowns"][field].items():
                lines.append(
                    f"| {group} | {int(summary['case_count'])} | "
                    f"{_metric(summary, f'recall_at_{max_k}')} | "
                    f"{_metric(summary, f'all_relevant_at_{max_k}')} | "
                    f"{_metric(summary, f'mrr_at_{max_k}')} |"
                )
            lines.append("")

        lines.extend([f"## Hybrid failure cases at K={max_k}", ""])
        failures = hybrid["failures_at_max_k"]
        if not failures:
            lines.append("No missing relevance labels at this cutoff.")
        else:
            lines.extend(
                [
                    "| Case | Missing labels | Retrieved ids | Question |",
                    "|---|---|---|---|",
                ]
            )
            for failure in failures:
                missing = ", ".join(failure["missing_source_ids_at_max_k"])
                retrieved = ", ".join(failure["retrieved_source_ids"])
                question = str(failure["question"]).replace("|", "\\|")
                lines.append(f"| {failure['case_id']} | {missing} | {retrieved} | {question} |")

    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "These figures are a deterministic regression baseline for this small curated corpus, not a "
            "production-search SLA or proof of general semantic retrieval quality. The hashing-vector "
            "ablation is educational; a production system should repeat the same evaluation with a real "
            "embedding model and a larger independently labelled dataset.",
            "",
        ]
    )
    return "\n".join(lines)


async def _run(args: argparse.Namespace) -> int:
    benchmark_path = Path(args.benchmark)
    corpus_path = Path(args.corpus)
    output_dir = Path(args.output_dir)
    cases = load_retrieval_cases(benchmark_path)
    corpus_ids = [
        json.loads(line)["id"]
        for line in corpus_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    validate_relevance_labels(cases, corpus_ids)
    ks = tuple(sorted(set(args.k)))
    modes = list(dict.fromkeys(args.mode))
    embedding_provider = None
    if args.embedding_provider == "openai-compatible":
        embedding_provider = OpenAICompatibleEmbeddingProvider(
            base_url=args.embedding_base_url,
            model=args.embedding_model,
            api_key_env=args.embedding_api_key_env,
            cache_path=args.embedding_cache_path,
            timeout_seconds=args.embedding_timeout_seconds,
            max_retries=args.embedding_max_retries,
            batch_size=args.embedding_batch_size,
        )
    evaluations: dict[str, object] = {}
    for mode in modes:
        searcher = SearcherAgent(
            corpus_path=corpus_path,
            enable_web_search=False,
            retrieval_mode=mode,
            result_limit=max(ks),
            embedding_provider=embedding_provider,
        )
        evaluations[mode] = await evaluate_searcher(searcher, cases, ks)

    embedding_status = (
        embedding_provider.status()
        if embedding_provider is not None
        else {"provider": "hashing", "dimensions": 64, "offline_safe": True}
    )

    payload: dict[str, object] = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark_path": benchmark_path.as_posix(),
        "benchmark_sha256": _sha256(benchmark_path),
        "corpus_path": corpus_path.as_posix(),
        "corpus_sha256": _sha256(corpus_path),
        "case_count": len(cases),
        "ks": list(ks),
        "embedding": embedding_status,
        "evaluations": evaluations,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "report.md").write_text(_render_markdown(payload), encoding="utf-8")
    with (output_dir / "case_results.jsonl").open("w", encoding="utf-8") as handle:
        for mode, evaluation in evaluations.items():
            for result in evaluation["case_results"]:
                handle.write(json.dumps({"mode": mode, **result}, ensure_ascii=False) + "\n")

    hybrid = evaluations.get("hybrid")
    if hybrid and args.min_hybrid_recall_at_max_k is not None:
        actual = hybrid["summary"][f"recall_at_{max(ks)}"]
        if actual < args.min_hybrid_recall_at_max_k:
            print(
                f"hybrid Recall@{max(ks)}={actual:.3f} is below "
                f"{args.min_hybrid_recall_at_max_k:.3f}"
            )
            return 2
    print(output_dir / "report.md")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate local retrieval quality and ablations.")
    parser.add_argument("--benchmark", default="data/benchmarks/researchbench.jsonl")
    parser.add_argument("--corpus", default="data/corpus/offline_corpus.jsonl")
    parser.add_argument("--output-dir", default="reports/retrieval_eval/latest")
    parser.add_argument(
        "--mode",
        action="append",
        choices=sorted(SearcherAgent.RETRIEVAL_MODES),
        default=None,
        help="Repeat to select modes. Defaults to lexical, vector, and hybrid.",
    )
    parser.add_argument("--k", type=int, action="append", default=None)
    parser.add_argument("--min-hybrid-recall-at-max-k", type=float)
    parser.add_argument(
        "--embedding-provider",
        choices=["hashing", "openai-compatible"],
        default="hashing",
    )
    parser.add_argument(
        "--embedding-base-url",
        default=os.getenv("EMBEDDING_BASE_URL", "https://api.openai.com/v1"),
    )
    parser.add_argument(
        "--embedding-model",
        default=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
    )
    parser.add_argument("--embedding-api-key-env", default="EMBEDDING_API_KEY")
    parser.add_argument(
        "--embedding-cache-path",
        default="data/memory/embedding_cache.sqlite3",
    )
    parser.add_argument("--embedding-timeout-seconds", type=float, default=30.0)
    parser.add_argument("--embedding-max-retries", type=int, default=2)
    parser.add_argument("--embedding-batch-size", type=int, default=64)
    args = parser.parse_args()
    args.mode = args.mode or ["lexical", "vector", "hybrid"]
    args.k = args.k or [1, 3, 5]
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
