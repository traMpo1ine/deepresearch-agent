from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SOURCE_REQUIREMENTS = {
    "project": [
        "README.md",
        "PROJECT_DESIGN.md",
        "pyproject.toml",
        "configs/default.toml",
        "configs/live_web.toml",
        "compose.redis.yml",
        "compose.yml",
        "Dockerfile",
        ".dockerignore",
        ".github/workflows/ci.yml",
        ".github/workflows/live-source-monitor.yml",
    ],
    "core code": [
        "src/deepresearch_agent/schemas/core.py",
        "src/deepresearch_agent/orchestration/coordinator.py",
        "src/deepresearch_agent/orchestration/dag.py",
        "src/deepresearch_agent/agents/planner.py",
        "src/deepresearch_agent/agents/searcher.py",
        "src/deepresearch_agent/agents/verifier.py",
        "src/deepresearch_agent/memory/sqlite_store.py",
        "src/deepresearch_agent/memory/vector_index.py",
        "src/deepresearch_agent/memory/embeddings.py",
        "src/deepresearch_agent/compression/textrank.py",
        "src/deepresearch_agent/evaluation/runner.py",
        "src/deepresearch_agent/evaluation/verifier_benchmark.py",
        "src/deepresearch_agent/evaluation/retrieval.py",
        "src/deepresearch_agent/showcase.py",
        "src/deepresearch_agent/resume_evidence.py",
        "src/deepresearch_agent/redblue_convergence.py",
        "src/deepresearch_agent/structured_output.py",
        "src/deepresearch_agent/claim_preflight.py",
        "src/deepresearch_agent/redblue_fixture_eval.py",
        "src/deepresearch_agent/llm/smoke_matrix.py",
        "src/deepresearch_agent/evaluation/real_judge_smoke.py",
        "src/deepresearch_agent/orchestration/stress_cases.py",
        "src/deepresearch_agent/web/app.py",
        "src/deepresearch_agent/web/run_store.py",
        "src/deepresearch_agent/web/metrics.py",
        "src/deepresearch_agent/web/upload_store.py",
        "src/deepresearch_agent/web/worker.py",
        "src/deepresearch_agent/web/static/index.html",
        "src/deepresearch_agent/web/static/app.js",
        "src/deepresearch_agent/web/static/styles.css",
        "src/deepresearch_agent/corpus_profiles.py",
        "src/deepresearch_agent/evaluation/llm_verifier_smoke.py",
        "src/deepresearch_agent/tools/web_search.py",
        "src/deepresearch_agent/tools/web_fetch.py",
        "src/deepresearch_agent/source_observability.py",
        "src/deepresearch_agent/live_source_history.py",
    ],
    "scripts": [
        "scripts/run_showcase.py",
        "scripts/run_research.py",
        "scripts/run_eval.py",
        "scripts/inspect_plan.py",
        "scripts/inspect_verification.py",
        "scripts/inspect_redblue.py",
        "scripts/inspect_report_trace.py",
        "scripts/inspect_resume_evidence.py",
        "scripts/inspect_orchestration_failure.py",
        "scripts/inspect_orchestration_stress.py",
        "scripts/inspect_redblue_convergence.py",
        "scripts/inspect_structured_output.py",
        "scripts/run_redblue_eval.py",
        "scripts/run_backend_smoke_matrix.py",
        "scripts/run_real_judge_smoke.py",
        "scripts/run_final_experiments.py",
        "scripts/inspect_llm_backend.py",
        "scripts/run_demo_server.py",
        "scripts/build_corpus_profiles.py",
        "scripts/run_llm_verifier_smoke.py",
        "scripts/run_formal_verifier_benchmark.py",
        "scripts/build_llm_verifier_extended_cases.py",
        "scripts/build_pre_resume_evidence_pack.py",
        "scripts/inspect_resume_metrics.py",
        "scripts/clean_artifacts.py",
        "scripts/inspect_web_search.py",
        "scripts/run_live_source_eval.py",
        "scripts/update_live_source_history.py",
        "scripts/run_retrieval_eval.py",
        "scripts/run_demo_worker.py",
        "scripts/run_golden_demo.py",
    ],
    "learning docs": [
        "docs/PROJECT_COMPLETION_LOG.md",
        "docs/FINAL_COMPLETION_CHECKLIST.md",
        "docs/FINAL_PROJECT_REPORT.md",
        "docs/BUILD_LOG.md",
        "docs/LEARNING_INDEX.md",
        "docs/INTERVIEW_QA.md",
        "docs/RESUME_NOTES.md",
        "docs/RESUME_SECOND_PROJECT_FINAL.md",
        "docs/TRACEABILITY_MATRIX.md",
        "docs/GITHUB_PORTFOLIO.md",
        "docs/EXPERIMENTS.md",
        "docs/learning_sqlite_migration.md",
        "docs/learning_orchestration_fallback.md",
        "docs/learning_redblue_convergence.md",
        "docs/learning_structured_output_fallback.md",
        "docs/learning_claim_preflight.md",
        "docs/generated/day09_orchestration_failure_trace.md",
        "docs/generated/day10_redblue_convergence_trace.md",
        "docs/generated/day11_orchestration_stress.md",
        "docs/generated/day12_structured_output_trace.md",
        "docs/assets/web_demo_walkthrough.gif",
        "docs/OPEN_SOURCE_COMPARISON.md",
        "docs/SHENZHEN_AGENT_INTERNSHIP_JD_2026.md",
        "docs/REAL_DATA_ARCHITECTURE.md",
        "docs/SERVICE_OPERATIONS.md",
        "docs/UPLOAD_INGESTION.md",
        "docs/RETRIEVAL_EVALUATION.md",
        "docs/EMBEDDING_INTEGRATION.md",
        "docs/DURABLE_WORKER_OPERATIONS.md",
        "docs/GOLDEN_DEMO.md",
    ],
    "datasets": [
        "data/benchmarks/researchbench.jsonl",
        "data/benchmarks/researchbench_extended.jsonl",
        "data/benchmarks/adversarial_researchbench.jsonl",
        "data/corpus/offline_corpus.jsonl",
        "data/corpus_profiles/local_kb_docs/README.md",
        "data/corpus/profiles/local_kb_docs.jsonl",
        "data/examples/verification_cases.jsonl",
        "data/examples/redblue_cases.jsonl",
        "data/examples/compression_cases.jsonl",
        "data/examples/memory_cases.jsonl",
        "data/examples/evaluation_cases.jsonl",
        "data/examples/structured_output_cases.jsonl",
        "data/examples/llm_verifier_cases.jsonl",
        "data/examples/llm_verifier_cases_extended.jsonl",
        "data/benchmarks/live_source_cases.jsonl",
        "data/benchmarks/retrieval_holdout_v1.jsonl",
        "data/benchmarks/retrieval_holdout_v1.meta.json",
    ],
}

GENERATED_REQUIREMENTS = {
    "showcase artifacts": [
        "reports/showcase/final_check/index.md",
        "reports/showcase/final_check/plan.md",
        "reports/showcase/final_check/report.md",
        "reports/showcase/final_check/report.json",
        "reports/showcase/final_check/memory_trace.md",
        "reports/showcase/final_check/compression_trace.md",
        "reports/showcase/final_check/verifier_trace.md",
        "reports/showcase/final_check/redblue_trace.md",
        "reports/showcase/final_check/llm_backend.md",
        "reports/showcase/final_check/eval_summary.md",
    ],
    "experiment artifacts": [
        "reports/experiments/20260702_162345_148429_researchbench_21c535de/summary.md",
        "reports/experiments/20260702_162345_148429_researchbench_21c535de/metrics.json",
        "reports/experiments/20260702_162345_148429_researchbench_21c535de/failure_cases.md",
        "reports/experiments/20260702_163315_852511_adversarial_f47f9b96/summary.md",
        "reports/experiments/20260702_163315_852511_adversarial_f47f9b96/metrics.json",
        "reports/experiments/20260702_163315_852511_adversarial_f47f9b96/failure_cases.md",
    ],
    "final evidence pack": [
        "reports/final/final_sprint_check/index.md",
        "reports/final/final_sprint_check/researchbench_summary.md",
        "reports/final/final_sprint_check/adversarial_summary.md",
        "reports/final/final_sprint_check/redblue_fixture_eval.md",
        "reports/final/final_sprint_check/structured_output_eval.md",
        "reports/final/final_sprint_check/backend_smoke_matrix.md",
        "reports/final/final_sprint_check/real_judge_smoke.md",
        "reports/final/final_sprint_check/completion_check.md",
    ],
    "formal verifier benchmark": [
        "reports/verifier_benchmark/formal_deepseek_v4_flash_120x3/report.md",
        "reports/verifier_benchmark/formal_deepseek_v4_flash_120x3/aggregate.json",
        "reports/verifier_benchmark/formal_deepseek_v4_flash_120x3/repetitions/run_01.json",
        "reports/verifier_benchmark/formal_deepseek_v4_flash_120x3/repetitions/run_02.json",
        "reports/verifier_benchmark/formal_deepseek_v4_flash_120x3/repetitions/run_03.json",
    ],
    "pre-resume evidence pack": [
        "reports/final/pre_resume_evidence_pack/index.md",
        "reports/final/pre_resume_evidence_pack/manifest.json",
        "reports/final/pre_resume_evidence_pack/extended_researchbench_summary.md",
        "reports/final/pre_resume_evidence_pack/extended_researchbench_metrics.json",
        "reports/final/pre_resume_evidence_pack/formal_verifier_benchmark.md",
        "reports/final/pre_resume_evidence_pack/formal_verifier_benchmark.json",
        "reports/final/pre_resume_evidence_pack/assets/web_demo_showcase.png",
    ],
    "retrieval benchmark": [
        "reports/retrieval_eval/benchmark_v3/report.md",
        "reports/retrieval_eval/benchmark_v3/summary.json",
        "reports/retrieval_eval/benchmark_v3/case_results.jsonl",
    ],
    "real embedding benchmark": [
        "reports/retrieval_eval/dashscope_text_embedding_v4_formal_v1/report.md",
        "reports/retrieval_eval/dashscope_text_embedding_v4_formal_v1/summary.json",
        "reports/retrieval_eval/dashscope_text_embedding_v4_formal_v1/case_results.jsonl",
    ],
    "retrieval holdout benchmark": [
        "reports/retrieval_eval/holdout_v1_hashing/report.md",
        "reports/retrieval_eval/holdout_v1_hashing/summary.json",
        "reports/retrieval_eval/holdout_v1_hashing/case_results.jsonl",
        "reports/retrieval_eval/holdout_v1_dashscope/report.md",
        "reports/retrieval_eval/holdout_v1_dashscope/summary.json",
        "reports/retrieval_eval/holdout_v1_dashscope/case_results.jsonl",
    ],
    "golden real-data demo": [
        "reports/golden_demo/v4/golden_summary.md",
        "reports/golden_demo/v4/golden_summary.json",
        "reports/golden_demo/v4/report.md",
        "reports/golden_demo/v4/report.json",
        "reports/golden_demo/v4/run_summary.json",
        "reports/golden_demo/v4/verifier_trace.md",
    ],
    "deepseek writer golden demo": [
        "reports/golden_demo/deepseek_v3/golden_summary.md",
        "reports/golden_demo/deepseek_v3/golden_summary.json",
        "reports/golden_demo/deepseek_v3/report.md",
        "reports/golden_demo/deepseek_v3/report.json",
        "reports/golden_demo/deepseek_v3/run_summary.json",
        "reports/golden_demo/deepseek_v3/verifier_trace.md",
        "reports/golden_demo/deepseek_v3/redblue_trace.md",
        "reports/golden_demo/deepseek_v3/llm_backend.md",
    ],
    "durable worker smoke": [
        "reports/worker_eval/e2e_v1/report.md",
        "reports/worker_eval/e2e_v1/summary.json",
    ],
}

EXPECTED_TEXT = {
    "README.md": [
        "项目介绍",
        "前端展示",
        "系统框架",
        "run_demo_server.py",
        "web_demo_walkthrough.gif",
        "Planner",
        "SQLite",
        "TextRank",
        "arXiv",
        "EMBEDDING_API_KEY",
        "DEEPSEEK_API_KEY",
        "run_golden_demo.py",
        "DeepSeek Writer",
        "Recall@5",
        "实验结果",
        "结论",
    ],
    "PROJECT_DESIGN.md": [
        "当前实验基线",
        "LLM Backend",
        "redblue judge mean",
    ],
    "docs/PROJECT_COMPLETION_LOG.md": [
        "项目完成过程总账",
        "遇到的问题",
        "怎么解决",
        "V3 正式实验冻结",
        "Resume-Targeted Mechanism Gap Closing",
        "不使用服务器",
    ],
    "docs/RESUME_NOTES.md": [
        "offline/mock benchmark",
        "3 分钟复试讲稿",
        "redblue repair_precision",
        "20260702_162345_148429_researchbench_21c535de",
        "Structured JSON fallback",
        "80 条 Red-Blue fixtures",
        "50 条 corrupted-output cases",
        "TRACEABILITY_MATRIX",
        "Web Demo",
        "LLM Verifier smoke",
        "Formal LLM Verifier benchmark",
        "Local corpus profiles",
        "Extended ResearchBench",
        "local_kb_docs",
        "Markdown/TXT/HTML/PDF",
    ],
    "docs/RESUME_SECOND_PROJECT_FINAL.md": [
        "DeepResearch Agent 简历第二项目最终版",
        "推荐简历 Bullet",
        "更短版本",
        "3 分钟面试讲稿",
        "必须诚实说明的边界",
    ],
    "docs/GITHUB_PORTFOLIO.md": [
        "GitHub Portfolio Checklist",
        "Repository Description",
        "Topics",
        "GitHub Profile",
        "First-Click Route",
    ],
    "docs/TRACEABILITY_MATRIX.md": [
        "简历证据追踪矩阵",
        "代码证据",
        "边界",
        "Web Demo App",
        "Formal LLM Verifier Benchmark",
        "Extended ResearchBench Coverage",
        "Local Corpus Profiles",
        "Markdown/TXT/HTML/PDF",
    ],
    "docs/FINAL_PROJECT_REPORT.md": [
        "最终项目报告",
        "正式实验结果",
        "结果边界",
        "20260702_162345_148429_researchbench_21c535de",
        "repair_oscillation",
        "Structured JSON fallback",
        "复试讲解摘要",
    ],
    "docs/FINAL_COMPLETION_CHECKLIST.md": [
        "V3 ResearchBench run",
        "20260702_163315_852511_adversarial_f47f9b96",
    ],
    "docs/EXPERIMENTS.md": [
        "2026-07-02 V3 Formal Offline Benchmark",
        "hotpot_style",
        "repair_convergence_rate",
        "repair_oscillation_rate",
    ],
    "docs/learning_structured_output_fallback.md": [
        "Level 1",
        "Level 2",
        "Level 3",
        "parse_success_rate",
    ],
    "docs/learning_claim_preflight.md": [
        "duplicate claim detection",
        "conflicting evidence detection",
        "overclaim downgrade",
    ],
    "docs/learning_sqlite_migration.md": [
        "PRAGMA user_version",
        "schema_version()",
        "旧库升级样例",
    ],
    "docs/learning_orchestration_fallback.md": [
        "TIMED_OUT",
        "batch_failure_events",
        "fallback report",
    ],
    "docs/learning_redblue_convergence.md": [
        "RepairLoopTrace",
        "OSCILLATION",
        "MAX_ROUNDS",
    ],
    "scripts/inspect_memory.py": [
        "--schema",
        "--runs",
        "database_summary",
    ],
    "scripts/inspect_report_trace.py": [
        "claim-citation-verification",
        "repair_actions",
        "Atomic Results",
    ],
    "scripts/run_eval.py": [
        "build_eval_run_id",
        "%f",
        "uuid4",
        "--group-by",
    ],
    "scripts/inspect_orchestration_failure.py": [
        "task_timeout",
        "batch_replan",
        "global_fallback",
    ],
    "scripts/inspect_orchestration_stress.py": [
        "orchestration stress scenarios",
        "summary",
    ],
    "scripts/inspect_structured_output.py": [
        "Structured output case id",
        "summary",
    ],
    "scripts/run_redblue_eval.py": [
        "Evaluate Red-Blue fixture repair success",
        "json",
    ],
    "scripts/run_backend_smoke_matrix.py": [
        "Run LLM backend dry-run/smoke matrix",
        "run-real",
    ],
    "scripts/inspect_redblue_convergence.py": [
        "oscillation",
        "converged",
        "max_rounds",
    ],
    "scripts/inspect_resume_evidence.py": [
        "--bullet",
        "resume_bullet",
    ],
    "src/deepresearch_agent/resume_evidence.py": [
        "ResumeEvidence",
        "learning_story",
        "boundary",
    ],
    "src/deepresearch_agent/agents/base.py": [
        "Unified agent entrypoint",
        "AgentResult",
    ],
    "src/deepresearch_agent/orchestration/coordinator.py": [
        "_run_agent",
        "AgentContext",
        "add_agent_event",
        "batch_failure_events",
        "repair_loop_trace",
    ],
    "src/deepresearch_agent/schemas/core.py": [
        "TIMED_OUT",
        "RepairLoopTrace",
        "repair_convergence_rate",
    ],
    "src/deepresearch_agent/structured_output.py": [
        "StructuredOutputParser",
        "parse_level",
        "schema defaults",
    ],
    "src/deepresearch_agent/claim_preflight.py": [
        "ClaimPreflight",
        "duplicate_claim_ids",
        "conflict_evidence_ids",
    ],
    "src/deepresearch_agent/redblue_fixture_eval.py": [
        "repair_success_before",
        "repair_success_after",
        "action_accuracy",
        "repair_precision",
        "per_source_of_error",
    ],
    "src/deepresearch_agent/llm/smoke_matrix.py": [
        "run_backend_smoke_matrix",
        "token_usage",
        "cost_estimate",
    ],
    "src/deepresearch_agent/evaluation/real_judge_smoke.py": [
        "run_real_judge_smoke",
        "JUDGE_SCHEMA",
        "Real judge smoke is separate",
    ],
    "scripts/run_real_judge_smoke.py": [
        "Run optional LLM-as-Judge smoke checks",
        "run-real",
    ],
    "scripts/run_final_experiments.py": [
        "Run the final reproducible project evidence pack",
        "redblue_fixture_eval",
        "structured_output_eval",
    ],
    "src/deepresearch_agent/orchestration/stress_cases.py": [
        "timeout_recovery_rate",
        "batch_replan_success_rate",
        "fallback_report_rate",
    ],
    "data/benchmarks/researchbench.jsonl": [
        "domain",
        "hotpot_style",
        "required_hops",
    ],
    "tests/unit/test_agent_run_interface.py": [
        "test_planner_searcher_reader_run_interfaces",
        "test_writer_verifier_critic_and_blue_run_interfaces",
    ],
    "tests/integration/test_mock_pipeline.py": [
        "list_agent_events",
        "planner",
        "verifier",
    ],
    "tests/unit/test_resume_evidence.py": [
        "test_resume_evidence_paths_are_real_project_evidence",
        "test_inspect_resume_evidence_cli_json",
    ],
    "tests/unit/test_v3_mechanisms.py": [
        "test_researchbench_v3_domain_and_hotpot_fields_are_complete",
        "test_redblue_convergence_cases_explain_stop_reasons",
    ],
    "src/deepresearch_agent/tools/web_fetch.py": [
        "validate_public_url",
        "extract_readable_text",
        "detect_prompt_injection",
        "_SafeRedirectHandler",
    ],
    "src/deepresearch_agent/corpus_profiles.py": [
        "SourceSection",
        "page_number",
        "citation_locator",
        "source_page_count",
    ],
    "src/deepresearch_agent/web/app.py": [
        "/api/health/live",
        "/api/health/ready",
        "X-Request-ID",
        "http_request",
        "demo_run_status",
        "run_store.list_recent",
    ],
    "src/deepresearch_agent/web/run_store.py": [
        "PRAGMA journal_mode=WAL",
        "idx_demo_runs_status_updated",
        "WHERE run_id = ? AND status = 'queued'",
        "recover_stale",
        "PRAGMA user_version",
        "request_fingerprint",
        "BEGIN IMMEDIATE",
        "RunCapacityError",
    ],
    "src/deepresearch_agent/web/metrics.py": [
        "deepresearch_http_requests_total",
        "deepresearch_http_request_duration_seconds_sum",
        "deepresearch_demo_runs",
        "deepresearch_demo_run_capacity",
    ],
    "src/deepresearch_agent/web/upload_store.py": [
        "64 * 1024",
        "UploadTooLargeError",
        "content_sha256",
        "PDF signature",
        "uploaded_content_sha256",
        "detect_prompt_injection",
    ],
    "Dockerfile": [
        "USER appuser",
        "HEALTHCHECK",
        "uvicorn",
    ],
    "src/deepresearch_agent/tools/web_search.py": [
        "ArxivSearchProvider",
        "GitHubSearchProvider",
        "DirectURLProvider",
        "RedisSearchCache",
        "FallbackSearchCache",
        "ResilientWebSearchProvider",
        "provider_telemetry",
    ],
    "scripts/run_live_source_eval.py": [
        "cache_hit_rate",
        "lineage_complete_rate",
        "expected_title_match",
        "transport_telemetry_complete_rate",
    ],
    "src/deepresearch_agent/live_source_history.py": [
        "p95_first_latency_seconds",
        "provider_retry_count",
        "failure_cases",
        "append_live_source_snapshot",
    ],
    ".github/workflows/live-source-monitor.yml": [
        "schedule",
        "actions/cache/restore",
        "actions/cache/save",
        "actions/upload-artifact",
        "--fail-on-error",
    ],
    "docs/REAL_DATA_ARCHITECTURE.md": [
        "SSRF",
        "content_sha256",
        "Redis",
        "live-source",
        "Provider 韧性与遥测",
    ],
}


@dataclass(slots=True)
class PathCheck:
    group: str
    path: str
    exists: bool
    bytes: int

    def to_dict(self) -> dict:
        return {
            "group": self.group,
            "path": self.path,
            "exists": self.exists,
            "bytes": self.bytes,
        }


@dataclass(slots=True)
class TextCheck:
    path: str
    phrase: str
    present: bool

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "phrase": self.phrase,
            "present": self.present,
        }


def collect_path_checks(root: Path, include_generated: bool = True) -> list[PathCheck]:
    requirements = dict(SOURCE_REQUIREMENTS)
    if include_generated:
        requirements.update(GENERATED_REQUIREMENTS)
    checks: list[PathCheck] = []
    for group, paths in requirements.items():
        for relative in paths:
            path = root / relative
            checks.append(
                PathCheck(
                    group=group,
                    path=relative,
                    exists=path.exists(),
                    bytes=path.stat().st_size if path.is_file() else 0,
                )
            )
    return checks


def collect_text_checks(root: Path) -> list[TextCheck]:
    checks: list[TextCheck] = []
    for relative, phrases in EXPECTED_TEXT.items():
        path = root / relative
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        for phrase in phrases:
            checks.append(TextCheck(path=relative, phrase=phrase, present=phrase in text))
    return checks


def build_completion_payload(root: Path, include_generated: bool = True) -> dict:
    path_checks = collect_path_checks(root, include_generated)
    text_checks = collect_text_checks(root)
    missing_paths = [check for check in path_checks if not check.exists]
    missing_text = [check for check in text_checks if not check.present]
    status = "passed" if not missing_paths and not missing_text else "failed"
    return {
        "status": status,
        "include_generated": include_generated,
        "path_checks": [check.to_dict() for check in path_checks],
        "text_checks": [check.to_dict() for check in text_checks],
        "summary": {
            "path_total": len(path_checks),
            "path_missing": len(missing_paths),
            "text_total": len(text_checks),
            "text_missing": len(missing_text),
        },
    }


def payload_to_markdown(payload: dict) -> str:
    lines = [
        "# DeepResearch Agent Completion Check",
        "",
        f"Status: `{payload['status']}`",
        f"Include generated artifacts: `{str(payload['include_generated']).lower()}`",
        "",
        "## Summary",
        "",
        f"- Path checks: `{payload['summary']['path_total']}`",
        f"- Missing paths: `{payload['summary']['path_missing']}`",
        f"- Text checks: `{payload['summary']['text_total']}`",
        f"- Missing text checks: `{payload['summary']['text_missing']}`",
        "",
        "## Missing Paths",
        "",
    ]
    missing_paths = [check for check in payload["path_checks"] if not check["exists"]]
    if missing_paths:
        for check in missing_paths:
            lines.append(f"- `{check['path']}` ({check['group']})")
    else:
        lines.append("- None.")
    lines.extend(["", "## Missing Text Checks", ""])
    missing_text = [check for check in payload["text_checks"] if not check["present"]]
    if missing_text:
        for check in missing_text:
            lines.append(f"- `{check['path']}` missing phrase: `{check['phrase']}`")
    else:
        lines.append("- None.")
    lines.extend(["", "## Checked Groups", ""])
    groups: dict[str, list[dict]] = {}
    for check in payload["path_checks"]:
        groups.setdefault(check["group"], []).append(check)
    for group, checks in groups.items():
        passed = sum(1 for check in checks if check["exists"])
        lines.append(f"- `{group}`: {passed}/{len(checks)} present")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check DeepResearch Agent final completion artifacts.")
    parser.add_argument("--source-only", action="store_true", help="Skip generated showcase/eval artifacts.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    parser.add_argument("--output", help="Optional path to write the report.")
    args = parser.parse_args()

    payload = build_completion_payload(ROOT, include_generated=not args.source_only)
    text = (
        json.dumps(payload, ensure_ascii=False, indent=2)
        if args.json
        else payload_to_markdown(payload)
    )
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    print(text)
    if payload["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
