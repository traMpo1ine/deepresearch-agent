from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from deepresearch_agent.evaluation.judge import BenchmarkCase, MockJudgeBackend
from deepresearch_agent.evaluation.runner import load_benchmark
from deepresearch_agent.llm import LLMBackendConfig, LLMMessage, backend_status, create_llm_backend
from deepresearch_agent.schemas import Claim, Evidence, ResearchReport, VerificationStatus
from deepresearch_agent.structured_output import StructuredOutputParser


JUDGE_SCHEMA = {
    "factuality": 0.0,
    "coverage": 0.0,
    "citation_quality": 0.0,
    "structure": 0.0,
    "usefulness": 0.0,
    "reason": "",
}


async def run_real_judge_smoke(
    backend_config: LLMBackendConfig,
    dataset_path: str | Path = "data/benchmarks/researchbench.jsonl",
    limit: int = 5,
    run_real: bool = False,
) -> dict[str, Any]:
    status = backend_status(backend_config)
    cases = load_benchmark(dataset_path)[:limit]
    should_call_backend = backend_config.backend == "mock" or (run_real and status["env_configured"])
    rows: list[dict[str, Any]] = []
    if not should_call_backend:
        return {
            "backend_status": status,
            "dataset": str(dataset_path),
            "limit": limit,
            "run_real": run_real,
            "attempted": 0,
            "successful": 0,
            "skipped_reason": "missing environment configuration or run_real=false",
            "rows": rows,
            "boundary": "Real judge smoke is separate from offline/mock ResearchBench metrics.",
        }

    backend = create_llm_backend(backend_config)
    mock_judge = MockJudgeBackend()
    for case in cases:
        report = _synthetic_report(case)
        started = time.perf_counter()
        if backend_config.backend == "mock":
            judge_score = await mock_judge.score(report, case)
            row = {
                "case_id": case.id,
                "success": True,
                "latency_seconds": time.perf_counter() - started,
                "scores": {
                    "factuality": judge_score.factuality,
                    "coverage": judge_score.coverage,
                    "citation_quality": judge_score.citation_quality,
                    "structure": judge_score.structure,
                    "usefulness": judge_score.usefulness,
                    "overall": judge_score.overall,
                },
                "parse_metadata": {"parse_ok": True, "parse_level": 1, "parse_error": None},
                "token_usage": {},
                "error": None,
            }
        else:
            row = await _score_with_backend(backend, case, report, started)
        rows.append(row)
    return {
        "backend_status": status,
        "dataset": str(dataset_path),
        "limit": limit,
        "run_real": run_real,
        "attempted": len(rows),
        "successful": sum(1 for row in rows if row["success"]),
        "skipped_reason": None,
        "rows": rows,
        "boundary": "Real judge smoke is separate from offline/mock ResearchBench metrics.",
    }


async def _score_with_backend(
    backend: Any,
    case: BenchmarkCase,
    report: ResearchReport,
    started: float,
) -> dict[str, Any]:
    prompt = "\n".join(
        [
            "Score this research report as JSON with numeric fields from 0 to 1:",
            "factuality, coverage, citation_quality, structure, usefulness, reason.",
            f"Question: {case.question}",
            f"Gold points: {case.gold_points}",
            "Report:",
            report.to_markdown(),
        ]
    )
    try:
        text = await backend.complete([LLMMessage(role="user", content=prompt)])
        parsed = StructuredOutputParser().parse(text, JUDGE_SCHEMA)
        scores = _normalize_scores(parsed.data)
        usage = getattr(backend, "last_usage", {})
        return {
            "case_id": case.id,
            "success": parsed.ok,
            "latency_seconds": time.perf_counter() - started,
            "scores": scores,
            "parse_metadata": parsed.metadata(),
            "token_usage": usage,
            "error": parsed.error,
        }
    except Exception as exc:  # noqa: BLE001 - smoke should report provider errors.
        return {
            "case_id": case.id,
            "success": False,
            "latency_seconds": time.perf_counter() - started,
            "scores": {},
            "parse_metadata": {"parse_ok": False, "parse_level": 0, "parse_error": str(exc)},
            "token_usage": getattr(backend, "last_usage", {}),
            "error": str(exc),
        }


def _synthetic_report(case: BenchmarkCase) -> ResearchReport:
    evidence = Evidence(
        task_id=f"task_{case.id}",
        title=f"Synthetic evidence for {case.id}",
        text="; ".join(case.gold_points),
        quote="; ".join(case.gold_points[:2]),
        source_id="synthetic_gold",
        chunk_id=f"chunk_{case.id}",
        score=1.0,
    )
    claim = Claim(
        text="; ".join(case.gold_points[:2]) or case.question,
        citation_ids=[evidence.id],
        confidence=0.8,
        verification_status=VerificationStatus.SUPPORTED,
    )
    return ResearchReport(
        question=case.question,
        title=f"Judge smoke report for {case.id}",
        summary="Synthetic report used only for judge smoke plumbing.",
        claims=[claim],
        evidence=[evidence],
        limitations=["This is a smoke test, not a formal benchmark result."],
    )


def _normalize_scores(data: dict[str, Any]) -> dict[str, float | str]:
    scores: dict[str, float | str] = {}
    values = []
    for field in ("factuality", "coverage", "citation_quality", "structure", "usefulness"):
        value = max(0.0, min(1.0, float(data.get(field, 0.0) or 0.0)))
        scores[field] = value
        values.append(value)
    scores["overall"] = sum(values) / len(values) if values else 0.0
    scores["reason"] = str(data.get("reason", ""))
    return scores


def real_judge_smoke_markdown(payload: dict[str, Any]) -> str:
    status = payload["backend_status"]
    lines = [
        "# Real LLM-as-Judge Smoke",
        "",
        f"Backend: `{status['backend']}`",
        f"Model: `{status['model']}`",
        f"Run real: `{payload['run_real']}`",
        f"Attempted: `{payload['attempted']}`",
        f"Successful: `{payload['successful']}`",
        f"Skipped reason: `{payload['skipped_reason'] or ''}`",
        "",
        "| case | success | overall | latency | parse_level | error |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['case_id']} | {row['success']} | "
            f"{float(row.get('scores', {}).get('overall', 0.0)):.3f} | "
            f"{row['latency_seconds']:.3f} | "
            f"{row.get('parse_metadata', {}).get('parse_level', 0)} | "
            f"{row.get('error') or ''} |"
        )
    lines.extend(["", payload["boundary"], "", "```json", json.dumps(payload, ensure_ascii=False, indent=2), "```"])
    return "\n".join(lines)
