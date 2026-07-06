from __future__ import annotations

import argparse
import json
from pathlib import Path


SCENARIOS = [
    {
        "topic": "citation tracking",
        "title": "Claim Citation Tracking",
        "fact": "DeepResearch Agent binds report claims to citation ids so each claim can be traced to evidence chunks and quotes.",
        "supported_claim": "DeepResearch Agent binds report claims to citation ids for evidence traceability.",
        "opposite_claim": "DeepResearch Agent treats citation ids as unnecessary for evidence traceability.",
        "extra_claim": "DeepResearch Agent binds claims to citation ids and automatically performs open-web search for every citation.",
        "unsupported_claim": "DeepResearch Agent deploys a mobile app for field data collection.",
    },
    {
        "topic": "sqlite memory",
        "title": "SQLite Shared Memory",
        "fact": "SQLite stores runs, tasks, evidence, claims, reports, verification traces, repair actions, and agent events for post-run inspection.",
        "supported_claim": "SQLite stores run traces, evidence, claims, and repair actions for post-run inspection.",
        "opposite_claim": "SQLite stores only the final answer and discards task and evidence traces.",
        "extra_claim": "SQLite stores run traces and also guarantees distributed multi-node scheduling.",
        "unsupported_claim": "SQLite provides GPU acceleration for model inference in the project.",
    },
    {
        "topic": "vector recall",
        "title": "Numpy Vector Recall",
        "fact": "The numpy vector index performs lightweight similarity recall, while SQLite remains the auditable memory store.",
        "supported_claim": "The numpy vector index is used for lightweight similarity recall.",
        "opposite_claim": "The numpy vector index replaces SQLite as the auditable memory store.",
        "extra_claim": "The numpy vector index performs similarity recall and uses a production FAISS cluster by default.",
        "unsupported_claim": "The numpy vector index is responsible for rendering the Web Demo tabs.",
    },
    {
        "topic": "textrank compression",
        "title": "TextRank Compression",
        "fact": "TextRank selects salient sentences and preserves citation quotes, but it remains a heuristic compressor.",
        "supported_claim": "TextRank compression selects salient sentences and preserves citation quotes.",
        "opposite_claim": "TextRank compression deliberately removes citation quotes from the context.",
        "extra_claim": "TextRank compression preserves citation quotes and guarantees that no relevant context is ever lost.",
        "unsupported_claim": "TextRank compression manages API key rotation for DeepSeek.",
    },
    {
        "topic": "verifier status",
        "title": "Atomic Verifier",
        "fact": "The verifier classifies claims as supported, partial, unsupported, or contradicted using citation presence, term overlap, quote overlap, and contradiction cues.",
        "supported_claim": "The verifier can classify claims as supported, partial, unsupported, or contradicted.",
        "opposite_claim": "The verifier only returns a single generic pass label for every claim.",
        "extra_claim": "The verifier classifies claims and serves as a mathematically complete proof system.",
        "unsupported_claim": "The verifier trains reinforcement learning policies with GRPO.",
    },
    {
        "topic": "redblue repair",
        "title": "Red-Blue Repair Actions",
        "fact": "Blue repair actions are limited to ADD, DELETE, MODIFY, and VERIFY, and each action records a target claim and reason.",
        "supported_claim": "Blue repair actions include ADD, DELETE, MODIFY, and VERIFY.",
        "opposite_claim": "Blue repair actions are unconstrained free-form edits with no target claim.",
        "extra_claim": "Blue repair actions include ADD, DELETE, MODIFY, VERIFY, and automatic database migration.",
        "unsupported_claim": "Blue repair actions create PowerPoint slides for papers.",
    },
    {
        "topic": "repair convergence",
        "title": "Repair Loop Trace",
        "fact": "RepairLoopTrace records convergence, oscillation detection, repair rounds, and stop reasons such as CONVERGED or MAX_ROUNDS.",
        "supported_claim": "RepairLoopTrace records convergence, oscillation detection, rounds, and stop reasons.",
        "opposite_claim": "RepairLoopTrace hides stop reasons and only stores the final report text.",
        "extra_claim": "RepairLoopTrace records convergence and also proves every repair loop will converge.",
        "unsupported_claim": "RepairLoopTrace manages browser viewport screenshots.",
    },
    {
        "topic": "structured output",
        "title": "Structured JSON Fallback",
        "fact": "StructuredOutputParser supports strict JSON, fenced or substring extraction, and common repair with schema defaults.",
        "supported_claim": "StructuredOutputParser supports strict JSON, extraction fallback, and schema-default repair.",
        "opposite_claim": "StructuredOutputParser fails immediately whenever the output is not strict JSON.",
        "extra_claim": "StructuredOutputParser repairs common JSON issues and guarantees semantic factual correctness.",
        "unsupported_claim": "StructuredOutputParser performs vector similarity search over evidence.",
    },
    {
        "topic": "claim preflight",
        "title": "Claim Preflight",
        "fact": "Claim Preflight flags duplicate claims, conflicting evidence hints, and overstrong assertions before final verification.",
        "supported_claim": "Claim Preflight can flag duplicate claims, conflicting evidence hints, and overstrong assertions.",
        "opposite_claim": "Claim Preflight intentionally ignores duplicate and overstrong claims.",
        "extra_claim": "Claim Preflight flags overstrong assertions and replaces the full verifier in all benchmarks.",
        "unsupported_claim": "Claim Preflight calculates DeepSeek token prices from API documentation.",
    },
    {
        "topic": "web demo",
        "title": "FastAPI Web Demo",
        "fact": "The Web Demo uses FastAPI with static HTML, CSS, and JavaScript to show Overview, Plan DAG, Report, Evidence & Memory, and Verification & Repair.",
        "supported_claim": "The Web Demo uses FastAPI and static frontend files to show the main research trace views.",
        "opposite_claim": "The Web Demo requires React and hides evidence and repair traces.",
        "extra_claim": "The Web Demo shows trace views and implements production multi-user authentication.",
        "unsupported_claim": "The Web Demo fine-tunes a language model during page load.",
    },
    {
        "topic": "demo runs",
        "title": "Background Demo Runs",
        "fact": "New demo runs are created through POST /api/runs, execute in a background task, and are polled until artifacts are ready.",
        "supported_claim": "New demo runs use a background task and polling before artifacts are displayed.",
        "opposite_claim": "New demo runs block the page until all artifacts are generated.",
        "extra_claim": "New demo runs use background polling and persist job state in a production database.",
        "unsupported_claim": "New demo runs upload private resumes to a third-party job board.",
    },
    {
        "topic": "deepseek smoke",
        "title": "DeepSeek Provider Smoke",
        "fact": "DeepSeek provider smoke is dry-run by default and requires run_real=true plus DEEPSEEK_API_KEY before making a real request.",
        "supported_claim": "DeepSeek provider smoke requires explicit real-run intent and a configured API key for real requests.",
        "opposite_claim": "DeepSeek provider smoke calls the real provider automatically by default.",
        "extra_claim": "DeepSeek provider smoke is dry-run by default and contributes to offline benchmark scores.",
        "unsupported_claim": "DeepSeek provider smoke builds local corpus profiles from Markdown folders.",
    },
    {
        "topic": "cost reporting",
        "title": "Provider Cost Reporting",
        "fact": "Real DeepSeek calls record prompt tokens, completion tokens, total tokens, cost_estimate_usd, and estimated_cost_rmb.",
        "supported_claim": "Real DeepSeek calls can record token usage and estimated RMB cost.",
        "opposite_claim": "Real DeepSeek calls never record token usage or cost estimates.",
        "extra_claim": "Real DeepSeek calls record token usage and guarantee a fixed response quality score.",
        "unsupported_claim": "Real DeepSeek calls control asyncio task scheduling in the coordinator.",
    },
    {
        "topic": "offline benchmark",
        "title": "Offline Benchmark Boundary",
        "fact": "Offline/mock benchmark metrics are kept separate from real provider smoke outputs to preserve reproducibility.",
        "supported_claim": "Offline benchmark metrics are kept separate from real provider smoke outputs.",
        "opposite_claim": "Real provider smoke outputs are mixed into official offline benchmark metrics.",
        "extra_claim": "Offline benchmark metrics are reproducible and therefore prove production generalization.",
        "unsupported_claim": "Offline benchmark metrics are generated from mobile sensor logs.",
    },
    {
        "topic": "extended benchmark",
        "title": "Extended ResearchBench",
        "fact": "The extended ResearchBench has 60 cases with balanced answer types: factual_explanation, multi_hop_reasoning, risk_analysis, technical_comparison, and solution_design.",
        "supported_claim": "The extended ResearchBench has 60 cases with five balanced answer types.",
        "opposite_claim": "The extended ResearchBench has only one answer type.",
        "extra_claim": "The extended ResearchBench has balanced answer types and covers every real-world research domain.",
        "unsupported_claim": "The extended ResearchBench stores browser screenshots for every case.",
    },
    {
        "topic": "ablation",
        "title": "Extended Ablation Run",
        "fact": "The extended ablation run compares baseline, verifier, redblue, and full profiles on the 60-case extended dataset.",
        "supported_claim": "The extended ablation run compares baseline, verifier, redblue, and full profiles.",
        "opposite_claim": "The extended ablation run contains no baseline profile.",
        "extra_claim": "The extended ablation run compares several profiles and includes production user traffic.",
        "unsupported_claim": "The extended ablation run performs image generation for UI assets.",
    },
    {
        "topic": "bootstrap ci",
        "title": "Bootstrap Confidence Interval",
        "fact": "Experiment summaries report judge_score_bootstrap_95_ci with judge_score_mean for benchmark profiles.",
        "supported_claim": "Experiment summaries include bootstrap 95% confidence intervals for judge scores.",
        "opposite_claim": "Experiment summaries omit uncertainty and report only raw final answers.",
        "extra_claim": "Bootstrap confidence intervals report uncertainty and prove the system is unbiased.",
        "unsupported_claim": "Bootstrap confidence intervals are used to resize the Web Demo sidebar.",
    },
    {
        "topic": "cohens d",
        "title": "Cohen Effect Size",
        "fact": "Cohen's d is reported as an offline profile comparison effect-size metric, not as production proof.",
        "supported_claim": "Cohen's d is used as an offline profile comparison effect-size metric.",
        "opposite_claim": "Cohen's d is treated as production proof in the project.",
        "extra_claim": "Cohen's d reports effect size and replaces all other benchmark metrics.",
        "unsupported_claim": "Cohen's d configures the DeepSeek base URL.",
    },
    {
        "topic": "local corpus profiles",
        "title": "Local Corpus Profiles",
        "fact": "Local corpus profiles build Searcher-compatible JSONL corpora from Markdown, TXT, and HTML source folders.",
        "supported_claim": "Local corpus profiles build Searcher-compatible JSONL corpora from local documents.",
        "opposite_claim": "Local corpus profiles require live open-web search for every run.",
        "extra_claim": "Local corpus profiles build JSONL corpora and implement online document permissions.",
        "unsupported_claim": "Local corpus profiles calculate Bootstrap confidence intervals.",
    },
    {
        "topic": "profile selection",
        "title": "Web Demo Corpus Selection",
        "fact": "The Web Demo can list corpus profiles and submit a selected corpus_profile when starting a mock run.",
        "supported_claim": "The Web Demo can submit a selected corpus profile when starting a mock run.",
        "opposite_claim": "The Web Demo always uses one hard-coded corpus and cannot list profiles.",
        "extra_claim": "The Web Demo selects corpus profiles and performs online user access control.",
        "unsupported_claim": "The Web Demo corpus selector changes the DeepSeek pricing table.",
    },
    {
        "topic": "rag boundary",
        "title": "RAG Retrieval Boundary",
        "fact": "The stable demo path uses local offline corpora and corpus profiles rather than full open-web search.",
        "supported_claim": "The stable retrieval path uses local offline corpora and corpus profiles.",
        "opposite_claim": "The stable retrieval path performs full open-web search by default.",
        "extra_claim": "The stable retrieval path uses local corpora and fully replaces production search infrastructure.",
        "unsupported_claim": "The stable retrieval path edits PowerPoint slide masters.",
    },
    {
        "topic": "state machine",
        "title": "Task State Machine",
        "fact": "The task state machine records lifecycle states such as pending, ready, running, succeeded, failed, blocked, and timed out.",
        "supported_claim": "The task state machine records task lifecycle states including failed, blocked, and timed out.",
        "opposite_claim": "The task state machine stores no failed or blocked states.",
        "extra_claim": "The task state machine records lifecycle states and guarantees no task can fail.",
        "unsupported_claim": "The task state machine estimates RMB cost for provider calls.",
    },
    {
        "topic": "dag orchestration",
        "title": "DAG Orchestration",
        "fact": "DAGTaskGraph represents task dependencies and supports topological batches for concurrent execution.",
        "supported_claim": "DAGTaskGraph represents dependencies and supports topological batch execution.",
        "opposite_claim": "DAGTaskGraph ignores dependencies and executes all tasks in arbitrary order.",
        "extra_claim": "DAGTaskGraph supports topological batches and distributed Kubernetes scheduling.",
        "unsupported_claim": "DAGTaskGraph parses malformed JSON model outputs.",
    },
    {
        "topic": "async semaphore",
        "title": "Async Concurrency Control",
        "fact": "The coordinator uses asyncio and Semaphore to limit concurrent agent task execution.",
        "supported_claim": "The coordinator uses asyncio and Semaphore to limit concurrent task execution.",
        "opposite_claim": "The coordinator launches unlimited concurrent tasks without any semaphore.",
        "extra_claim": "The coordinator limits concurrency and guarantees external APIs never fail.",
        "unsupported_claim": "The coordinator uses Semaphore to calculate Cohen's d.",
    },
    {
        "topic": "showcase pack",
        "title": "Showcase Artifact Pack",
        "fact": "build_showcase writes plan, report, run summary, memory trace, compression trace, verifier trace, redblue trace, backend notes, and interview notes.",
        "supported_claim": "build_showcase writes report, trace, verifier, redblue, and backend artifact files.",
        "opposite_claim": "build_showcase writes no trace files and only prints to the console.",
        "extra_claim": "build_showcase writes trace artifacts and deploys them to a public cloud service.",
        "unsupported_claim": "build_showcase trains an embedding model from scratch.",
    },
    {
        "topic": "memory trace",
        "title": "Memory Trace",
        "fact": "The memory trace records cited evidence and vector recall hits for post-run inspection.",
        "supported_claim": "The memory trace records cited evidence and vector recall hits.",
        "opposite_claim": "The memory trace hides cited evidence and vector recall hits.",
        "extra_claim": "The memory trace records cited evidence and performs legal compliance review.",
        "unsupported_claim": "The memory trace sets the FastAPI server port.",
    },
    {
        "topic": "failure cases",
        "title": "Failure Case Report",
        "fact": "Experiment reports include failure cases such as claims requiring stronger support.",
        "supported_claim": "Experiment reports include failure cases for claims requiring stronger support.",
        "opposite_claim": "Experiment reports intentionally omit failure cases.",
        "extra_claim": "Experiment reports include failure cases and automatically prove every future run will pass.",
        "unsupported_claim": "Experiment reports configure browser screenshots.",
    },
    {
        "topic": "artifact paths",
        "title": "Web Artifact API",
        "fact": "The Web Demo exposes artifact paths and structured payloads for plan, report, memory, verifier, redblue, eval, and backend data.",
        "supported_claim": "The Web Demo exposes structured artifact data for plan, report, memory, verifier, redblue, eval, and backend views.",
        "opposite_claim": "The Web Demo exposes no structured artifact data.",
        "extra_claim": "The Web Demo exposes artifact data and stores user accounts in a production database.",
        "unsupported_claim": "The Web Demo artifact API generates benchmark cases automatically.",
    },
    {
        "topic": "api key safety",
        "title": "API Key Safety",
        "fact": "Real provider calls read API keys from environment variables and do not require keys to be written into project files.",
        "supported_claim": "Real provider calls read API keys from environment variables.",
        "opposite_claim": "Real provider calls require hard-coded API keys in source files.",
        "extra_claim": "Real provider calls read environment variables and automatically rotate keys across accounts.",
        "unsupported_claim": "API key safety controls TextRank sentence scoring.",
    },
    {
        "topic": "portfolio boundary",
        "title": "Portfolio Demo Boundary",
        "fact": "The current system is a local portfolio demo and reproducible engineering project, not a production multi-tenant SaaS.",
        "supported_claim": "The current system is a local portfolio demo rather than a production multi-tenant SaaS.",
        "opposite_claim": "The current system is already a production multi-tenant SaaS.",
        "extra_claim": "The current system is a local portfolio demo and already supports enterprise billing.",
        "unsupported_claim": "The portfolio boundary determines vector cosine similarity.",
    },
]


def build_cases() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, scenario in enumerate(SCENARIOS, start=1):
        base_id = f"lve_{index:03d}"
        fact = scenario["fact"]
        title = scenario["title"]
        rows.extend(
            [
                _row(f"{base_id}_s", scenario["supported_claim"], title, fact, fact, "supported"),
                _row(f"{base_id}_c", scenario["opposite_claim"], title, fact, fact, "contradicted"),
                _row(f"{base_id}_p", scenario["extra_claim"], title, fact, fact, "partial"),
                _row(f"{base_id}_u", scenario["unsupported_claim"], title, fact, fact, "unsupported"),
            ]
        )
    return rows


def _row(
    case_id: str,
    claim: str,
    evidence_title: str,
    evidence_text: str,
    quote: str,
    expected_status: str,
) -> dict[str, str]:
    return {
        "id": case_id,
        "claim": claim,
        "evidence_title": evidence_title,
        "evidence_text": evidence_text,
        "quote": quote,
        "expected_status": expected_status,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build deterministic extended LLM verifier smoke cases.")
    parser.add_argument("--output", default="data/examples/llm_verifier_cases_extended.jsonl")
    args = parser.parse_args()
    rows = build_cases()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(rows)} cases to {output}")


if __name__ == "__main__":
    main()
