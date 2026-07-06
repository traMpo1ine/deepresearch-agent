import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from deepresearch_agent.evaluation.runner import load_benchmark, summarize_results
from deepresearch_agent.redblue_convergence import inspect_convergence_case
from deepresearch_agent.schemas import EvaluationResult, JudgeScore


ALLOWED_DOMAINS = {
    "agent_orchestration",
    "memory_retrieval",
    "citation_verification",
    "redblue_repair",
    "evaluation",
    "llm_backend",
    "context_compression",
    "rag_system",
    "reliability",
    "multi_hop",
    "engineering_tradeoff",
}


def test_researchbench_v3_domain_and_hotpot_fields_are_complete() -> None:
    rows = [
        json.loads(line)
        for line in Path("data/benchmarks/researchbench.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert len(rows) == 35
    assert all(row["domain"] in ALLOWED_DOMAINS for row in rows)
    assert all("required_hops" in row and "hotpot_style" in row for row in rows)
    domain_counts = Counter(row["domain"] for row in rows)
    assert set(domain_counts) == ALLOWED_DOMAINS
    assert min(domain_counts.values()) >= 2
    assert sum(1 for row in rows if row["required_hops"] >= 2) >= 8
    assert sum(1 for row in rows if row["hotpot_style"]) >= 5


def test_load_benchmark_exposes_domain_and_hotpot_fields() -> None:
    cases = load_benchmark("data/benchmarks/researchbench.jsonl")
    hotpot_cases = [case for case in cases if case.hotpot_style]

    assert hotpot_cases
    assert hotpot_cases[0].required_hops >= 2
    assert hotpot_cases[0].domain in ALLOWED_DOMAINS


def test_summarize_results_includes_domain_and_subset_metrics() -> None:
    result = EvaluationResult(
        question_id="x",
        factual_accuracy=1.0,
        hallucination_rate=0.0,
        citation_coverage=1.0,
        unsupported_claim_rate=0.0,
        judge_score=JudgeScore(1, 1, 1, 1, 1),
        domain="multi_hop",
        required_hops=2,
        hotpot_style=True,
        repair_convergence_rate=1.0,
        avg_repair_rounds=1.0,
    )

    summary = summarize_results([result])

    assert summary["per_domain"]["multi_hop"]["n"] == 1
    assert summary["multi_hop_subset"]["n"] == 1
    assert summary["hotpot_style_subset"]["n"] == 1
    assert summary["repair_convergence_rate"] == 1.0
    assert summary["avg_repair_rounds"] == 1.0


def test_redblue_convergence_cases_explain_stop_reasons() -> None:
    converged = inspect_convergence_case("converged")
    oscillation = inspect_convergence_case("oscillation")

    assert converged["stop_reason"] == "CONVERGED"
    assert converged["converged"] is True
    assert oscillation["stop_reason"] == "OSCILLATION"
    assert oscillation["oscillating"] is True


def test_v3_inspection_scripts_run() -> None:
    orchestration = subprocess.run(
        [
            sys.executable,
            "scripts/inspect_orchestration_failure.py",
            "--case",
            "batch_replan",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    convergence = subprocess.run(
        [
            sys.executable,
            "scripts/inspect_redblue_convergence.py",
            "--case",
            "oscillation",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(orchestration.stdout)["replan_count"] == 1
    assert json.loads(convergence.stdout)["stop_reason"] == "OSCILLATION"
