from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from deepresearch_agent.agents.planner import PlannerAgent
from deepresearch_agent.compression import TextRankCompressor
from deepresearch_agent.evaluation_cases import (
    evaluation_payload_to_markdown,
    get_evaluation_example_set,
    inspect_evaluation_case,
)
from deepresearch_agent.llm import LLMBackendConfig, backend_status
from deepresearch_agent.memory import NumpyVectorIndex, SQLiteMemoryStore
from deepresearch_agent.orchestration.coordinator import ResearchCoordinator
from deepresearch_agent.orchestration.inspection import plan_to_markdown
from deepresearch_agent.schemas import ResearchReport


@dataclass(slots=True)
class ShowcaseResult:
    output_dir: Path
    run_id: str
    files: dict[str, Path]


async def build_showcase(
    question: str,
    output_dir: str | Path | None = None,
    planner_mode: str = "heuristic",
    max_concurrency: int = 4,
    repair_rounds: int = 2,
    llm_backend: str = "mock",
    model: str | None = None,
    timeout_seconds: float = 60.0,
    max_retries: int = 2,
    vllm_base_url: str = "http://localhost:8000/v1",
    corpus_path: str | Path = "data/corpus/offline_corpus.jsonl",
    use_iterative_search: bool = False,
    max_follow_up_queries: int = 1,
    source_quality_threshold: float = 0.58,
    enable_web_search: bool = False,
    web_search_provider: str = "disabled",
    max_web_results: int = 3,
    embedding_provider: str = "hashing",
    embedding_base_url: str = "https://api.openai.com/v1",
    embedding_model: str = "text-embedding-3-small",
    embedding_api_key_env: str = "EMBEDDING_API_KEY",
    embedding_cache_path: str | Path | None = None,
    embedding_timeout_seconds: float = 30.0,
    embedding_max_retries: int = 2,
    embedding_batch_size: int = 64,
    writer_mode: str = "template",
) -> ShowcaseResult:
    target_dir = _resolve_output_dir(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    memory_path = target_dir / "memory.sqlite3"
    vector_path = target_dir / "vector_index.npz"
    plan_dir = target_dir / "plans"
    plan_dir.mkdir(parents=True, exist_ok=True)

    plan = await PlannerAgent(mode=planner_mode).plan(question)
    coordinator = ResearchCoordinator(
        max_concurrency=max_concurrency,
        memory_path=memory_path,
        vector_path=vector_path,
        plan_dir=plan_dir,
        repair_rounds=repair_rounds,
        planner_mode=planner_mode,
        llm_backend=llm_backend,
        model=model,
        llm_timeout_seconds=timeout_seconds,
        llm_max_retries=max_retries,
        llm_vllm_base_url=vllm_base_url,
        corpus_path=corpus_path,
        use_iterative_search=use_iterative_search,
        max_follow_up_queries=max_follow_up_queries,
        source_quality_threshold=source_quality_threshold,
        enable_web_search=enable_web_search,
        web_search_provider=web_search_provider,
        max_web_results=max_web_results,
        web_search_cache_path=target_dir / "web_search_cache.sqlite3",
        embedding_provider=embedding_provider,
        embedding_base_url=embedding_base_url,
        embedding_model=embedding_model,
        embedding_api_key_env=embedding_api_key_env,
        embedding_cache_path=embedding_cache_path or target_dir / "embedding_cache.sqlite3",
        embedding_timeout_seconds=embedding_timeout_seconds,
        embedding_max_retries=embedding_max_retries,
        embedding_batch_size=embedding_batch_size,
        writer_mode=writer_mode,
    )
    report = await coordinator.run(question)
    run_id = report.run_id or "run_unknown"

    files = {
        "plan_md": target_dir / "plan.md",
        "report_md": target_dir / "report.md",
        "report_json": target_dir / "report.json",
        "run_summary_json": target_dir / "run_summary.json",
        "memory_trace_md": target_dir / "memory_trace.md",
        "compression_trace_md": target_dir / "compression_trace.md",
        "verifier_trace_md": target_dir / "verifier_trace.md",
        "redblue_trace_md": target_dir / "redblue_trace.md",
        "llm_backend_md": target_dir / "llm_backend.md",
        "eval_summary_md": target_dir / "eval_summary.md",
        "interview_notes_md": target_dir / "interview_notes.md",
        "index_md": target_dir / "index.md",
    }
    files["plan_md"].write_text(plan_to_markdown(plan), encoding="utf-8")
    files["report_md"].write_text(report.to_markdown(), encoding="utf-8")
    files["report_json"].write_text(report.to_json(), encoding="utf-8")
    files["run_summary_json"].write_text(
        json.dumps(report.run_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    files["memory_trace_md"].write_text(
        _memory_trace_markdown(question, memory_path, vector_path, report),
        encoding="utf-8",
    )
    files["compression_trace_md"].write_text(
        _compression_trace_markdown(question, report),
        encoding="utf-8",
    )
    files["verifier_trace_md"].write_text(_verifier_trace_markdown(report), encoding="utf-8")
    files["redblue_trace_md"].write_text(_redblue_trace_markdown(report), encoding="utf-8")
    files["llm_backend_md"].write_text(
        _llm_backend_markdown(
            LLMBackendConfig(
                backend=llm_backend,
                model=model,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
                vllm_base_url=vllm_base_url,
            ),
            report,
            corpus_path,
        ),
        encoding="utf-8",
    )
    files["eval_summary_md"].write_text(
        evaluation_payload_to_markdown(
            inspect_evaluation_case(get_evaluation_example_set("baseline_vs_redblue"))
        ),
        encoding="utf-8",
    )
    files["interview_notes_md"].write_text(_interview_notes_markdown(question, report), encoding="utf-8")
    files["index_md"].write_text(_index_markdown(question, run_id, files), encoding="utf-8")
    return ShowcaseResult(output_dir=target_dir, run_id=run_id, files=files)


def _resolve_output_dir(output_dir: str | Path | None) -> Path:
    if output_dir:
        return Path(output_dir)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("reports") / "showcase" / stamp


def _memory_trace_markdown(
    question: str,
    memory_path: Path,
    vector_path: Path,
    report: ResearchReport,
) -> str:
    store = SQLiteMemoryStore(memory_path)
    vector_index = NumpyVectorIndex.load(vector_path) if vector_path.exists() else NumpyVectorIndex()
    vector_hits = vector_index.search(question, top_k=5)
    lines = [
        "# Showcase Memory Trace",
        "",
        f"Run id: `{report.run_id}`",
        f"Memory path: `{memory_path}`",
        f"Vector path: `{vector_path}`",
        f"Evidence in report: `{len(report.evidence)}`",
        f"Claims in report: `{len(report.claims)}`",
        "",
        "## Cited Evidence",
        "",
    ]
    cited = sorted({cid for claim in report.claims for cid in claim.citation_ids})
    if not cited:
        lines.append("- No cited evidence ids were attached.")
    for evidence_id in cited:
        item = store.get_evidence(evidence_id)
        if item is None:
            lines.append(f"- `{evidence_id}` was not found in SQLite.")
        else:
            locator = item.metadata.get("citation_locator", "n/a")
            lines.append(
                f"- `{evidence_id}` {item.title} | source={item.source_id} "
                f"| locator={locator} | quote={item.quote}"
            )
    lines.extend(["", "## Vector Recall", ""])
    if not vector_hits:
        lines.append("- No vector hits.")
    for evidence_id, score in vector_hits:
        item = store.get_evidence(evidence_id)
        title = item.title if item else "missing"
        quote = item.quote if item else None
        lines.append(f"- `{evidence_id}` score={score:.3f} title={title} quote={quote}")
    return "\n".join(lines)


def _compression_trace_markdown(question: str, report: ResearchReport) -> str:
    context = TextRankCompressor().compress_evidence(question, report.evidence)
    lines = [
        "# Showcase Compression Trace",
        "",
        f"Question: {question}",
        f"Original chars: `{context.original_char_count}`",
        f"Compressed chars: `{context.compressed_char_count}`",
        f"Compression ratio: `{context.compression_ratio:.3f}`",
        f"Selected sentences: `{len(context.sentences)}`",
        "",
        "## Selected Sentences",
        "",
    ]
    for index, sentence in enumerate(context.sentences, start=1):
        lines.extend(
            [
                f"### Sentence {index}",
                "",
                sentence.text,
                "",
                f"Evidence: `{sentence.evidence_id}`",
                f"Source: `{sentence.source_id}`",
                f"Preserved quote: `{str(sentence.preserved_quote).lower()}`",
                f"Score: `{sentence.score:.3f}`",
                "",
            ]
        )
    return "\n".join(lines)


def _verifier_trace_markdown(report: ResearchReport) -> str:
    lines = ["# Showcase Verifier Trace", ""]
    if not report.claims:
        return "# Showcase Verifier Trace\n\nNo claims were produced."
    for claim_index, claim in enumerate(report.claims, start=1):
        trace = claim.verification_trace
        lines.extend(
            [
                f"## Claim {claim_index}",
                "",
                claim.text,
                "",
                f"Status: `{claim.verification_status.value}`",
                f"Confidence: `{claim.confidence:.2f}`",
                f"Citations: `{claim.citation_ids}`",
                f"Reason: {claim.verification_reason}",
                "",
            ]
        )
        if not trace:
            lines.append("No verification trace was attached.")
            lines.append("")
            continue
        for atomic_index, atomic in enumerate(trace.atomic_results, start=1):
            lines.extend(
                [
                    f"### Atomic {atomic_index}",
                    "",
                    atomic.text,
                    "",
                    f"Status: `{atomic.status.value}`",
                    f"Best evidence: `{atomic.evidence_id}`",
                    f"Term overlap: `{atomic.term_overlap:.2f}`",
                    f"Quote overlap: `{atomic.quote_overlap:.2f}`",
                    f"Missing terms: `{atomic.missing_terms}`",
                    f"Decision: {atomic.decision_reason}",
                    "",
                ]
            )
    return "\n".join(lines)


def _redblue_trace_markdown(report: ResearchReport) -> str:
    lines = ["# Showcase Red-Blue Trace", ""]
    if report.repair_loop_trace:
        lines.extend(
            [
                "## Repair Loop Trace",
                "",
                "| round | findings | weak claims | actions | converged | oscillating | stop |",
                "|---:|---:|---:|---:|---|---|---|",
            ]
        )
        for trace in report.repair_loop_trace:
            lines.append(
                f"| {trace.round_index} | {trace.finding_count} | {trace.weak_claim_count} | "
                f"{trace.repair_action_count} | {trace.converged} | {trace.oscillating} | "
                f"{trace.stop_reason} |"
            )
        lines.append("")
    if not report.repair_actions:
        lines.extend(["No Red-Blue repair actions were needed for this run.", ""])
        return "\n".join(lines)
    for index, action in enumerate(report.repair_actions, start=1):
        lines.extend(
            [
                f"## Action {index}",
                "",
                f"Type: `{action.action_type.value}`",
                f"Target: `{action.target_claim_id}`",
                f"Reason: {action.reason}",
                f"Patch: {action.patch}",
                f"Before: {action.before}",
                f"After: {action.after}",
                "",
            ]
        )
    return "\n".join(lines)


def _llm_backend_markdown(
    config: LLMBackendConfig,
    report: ResearchReport,
    corpus_path: str | Path,
) -> str:
    status = backend_status(config)
    lines = [
        "# Showcase LLM Backend",
        "",
        f"Backend: `{status['backend']}`",
        f"Model: `{status['model']}`",
        f"Base URL: `{status['base_url']}`",
        f"Timeout seconds: `{status['timeout_seconds']}`",
        f"Max retries: `{status['max_retries']}`",
        f"Env var: `{status['env_var']}`",
        f"Env configured: `{str(status['env_configured']).lower()}`",
        f"Offline safe: `{str(status['offline_safe']).lower()}`",
        "",
        "## Run Summary Backend Fields",
        "",
        f"- llm_backend: `{report.run_summary.get('llm_backend')}`",
        f"- model: `{report.run_summary.get('model')}`",
        f"- llm_timeout_seconds: `{report.run_summary.get('llm_timeout_seconds')}`",
        f"- llm_max_retries: `{report.run_summary.get('llm_max_retries')}`",
        f"- llm_vllm_base_url: `{report.run_summary.get('llm_vllm_base_url')}`",
        f"- corpus_path: `{corpus_path}`",
        "",
        "The showcase records backend configuration, but offline/mock benchmark metrics must not be mixed with real LLM outputs.",
    ]
    return "\n".join(lines)


def _interview_notes_markdown(question: str, report: ResearchReport) -> str:
    summary = report.run_summary
    return "\n".join(
        [
            "# Showcase Interview Notes",
            "",
            f"Question: {question}",
            "",
            "## 60-Second Story",
            "",
            (
                "This run demonstrates the full DeepResearch pipeline: Planner builds a DAG, "
                "Coordinator executes search/read tasks with memory and compression, Writer emits "
                "cited claims, Verifier checks atomic claim grounding, and Red-Blue records repair actions."
            ),
            "",
            "## Numbers To Mention",
            "",
            f"- run id: `{report.run_id}`",
            f"- tasks: `{summary.get('task_count', 0)}`",
            f"- evidence: `{summary.get('evidence_count', 0)}`",
            f"- recalled evidence: `{summary.get('recalled_evidence_count', 0)}`",
            f"- live sources: `{summary.get('live_sources', {}).get('source_count', 0)}`",
            f"- live-source lineage complete rate: `{summary.get('live_sources', {}).get('lineage_complete_rate', 0.0)}`",
            f"- live-source cache hit rate: `{summary.get('live_sources', {}).get('cache_hit_rate', 0.0)}`",
            f"- provider operational rate: `{summary.get('web_search_telemetry', {}).get('summary', {}).get('operational_rate', 0.0)}`",
            f"- provider retries: `{summary.get('web_search_telemetry', {}).get('summary', {}).get('total_retries', 0)}`",
            f"- circuit-open events: `{summary.get('web_search_telemetry', {}).get('summary', {}).get('circuit_open_count', 0)}`",
            f"- compression ratio: `{summary.get('compression_ratio', 1.0):.3f}`",
            f"- repair actions: `{summary.get('repair_count', 0)}`",
            f"- planner mode: `{summary.get('planner_mode', 'unknown')}`",
            f"- llm backend: `{summary.get('llm_backend', 'unknown')}`",
            f"- writer mode: `{summary.get('writer_mode', 'unknown')}`",
            f"- embedding provider: `{summary.get('embedding_telemetry', {}).get('provider', 'unknown')}`",
            f"- embedding model: `{summary.get('embedding_telemetry', {}).get('model', 'unknown')}`",
            f"- embedding remote inputs: `{summary.get('embedding_telemetry', {}).get('remote_inputs', 0)}`",
            f"- embedding cache hits: `{summary.get('embedding_telemetry', {}).get('cache_hits', 0)}`",
            "",
            "## Tradeoff",
            "",
            (
                "The showcase remains offline by default. This keeps the demo reproducible and lets "
                "the engineering mechanisms be inspected without API cost or model nondeterminism."
            ),
        ]
    )


def _index_markdown(question: str, run_id: str, files: dict[str, Path]) -> str:
    lines = [
        "# DeepResearch Showcase Pack",
        "",
        f"Question: {question}",
        f"Run id: `{run_id}`",
        "",
        "## Artifacts",
        "",
    ]
    for name, path in files.items():
        if name == "index_md":
            continue
        lines.append(f"- `{name}`: [{path.name}]({path.name})")
    return "\n".join(lines)
