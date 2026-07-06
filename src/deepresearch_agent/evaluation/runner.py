from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from deepresearch_agent.config import config_get
from deepresearch_agent.evaluation.judge import BenchmarkCase, JudgeBackend, MockJudgeBackend
from deepresearch_agent.evaluation.metrics import bootstrap_ci, cohens_d
from deepresearch_agent.orchestration import ResearchCoordinator
from deepresearch_agent.schemas import EvaluationResult, ResearchReport, VerificationStatus


@dataclass(slots=True)
class ExperimentConfig:
    name: str
    use_memory_recall: bool
    use_compression: bool
    use_verifier: bool
    use_redblue: bool
    planner_mode: str = "heuristic"


@dataclass(slots=True)
class EvalIntegrityReport:
    config_snapshot: dict
    dataset_summary: dict
    suite_source_counts: dict[str, int]
    payload_validation_status: str
    payload_validation_error: str | None
    experiment_artifacts: dict[str, dict[str, str]]

    def to_dict(self) -> dict:
        return {
            "config_snapshot": self.config_snapshot,
            "dataset_summary": self.dataset_summary,
            "suite_source_counts": self.suite_source_counts,
            "payload_validation_status": self.payload_validation_status,
            "payload_validation_error": self.payload_validation_error,
            "experiment_artifacts": self.experiment_artifacts,
        }


SUMMARY_MEAN_FIELDS = (
    "factual_accuracy",
    "hallucination_rate",
    "weak_support_rate",
    "citation_coverage",
    "evidence_reuse_rate",
    "compression_ratio",
    "repair_success_rate",
    "atomic_support_rate",
    "contradiction_detection_rate",
    "repair_precision",
    "repair_coverage",
    "repair_convergence_rate",
    "repair_oscillation_rate",
    "avg_repair_rounds",
    "evidence_grounding_score",
    "avg_task_latency",
)

REQUIRED_RESULT_FIELDS = {
    "question_id",
    "answer_type",
    "factual_accuracy",
    "hallucination_rate",
    "weak_support_rate",
    "citation_coverage",
    "unsupported_claim_rate",
    "evidence_reuse_rate",
    "compression_ratio",
    "repair_success_rate",
    "atomic_support_rate",
    "contradiction_detection_rate",
    "repair_precision",
    "repair_coverage",
    "repair_convergence_rate",
    "repair_oscillation_rate",
    "avg_repair_rounds",
    "evidence_grounding_score",
    "avg_task_latency",
    "domain",
    "required_hops",
    "hotpot_style",
    "repair_action_counts",
    "failure_analysis",
    "judge_score",
    "bootstrap_ci",
    "cohens_d",
}

REQUIRED_JUDGE_FIELDS = {
    "factuality",
    "coverage",
    "citation_quality",
    "structure",
    "usefulness",
    "overall",
}


def default_experiment_configs() -> dict[str, ExperimentConfig]:
    return {
        "baseline": ExperimentConfig("baseline", False, False, False, False, "template"),
        "memory": ExperimentConfig("+memory", True, False, False, False, "heuristic"),
        "compression": ExperimentConfig("+compression", True, True, False, False, "heuristic"),
        "verifier": ExperimentConfig("+verifier", True, True, True, False, "heuristic"),
        "redblue": ExperimentConfig("+redblue", True, True, True, True, "heuristic"),
        "full": ExperimentConfig("full", True, True, True, True, "heuristic"),
    }


EXPERIMENT_CONFIGS: dict[str, ExperimentConfig] = default_experiment_configs()


def experiment_configs_from_config(config: dict | None) -> dict[str, ExperimentConfig]:
    profiles = config_get(config or {}, "experiments.profiles", [])
    if not profiles:
        return default_experiment_configs()
    configs: dict[str, ExperimentConfig] = {}
    for raw in profiles:
        key = raw.get("key")
        if not key:
            raise ValueError("Experiment profile is missing required key.")
        configs[str(key)] = ExperimentConfig(
            name=str(raw.get("name", key)),
            use_memory_recall=bool(raw.get("use_memory_recall", False)),
            use_compression=bool(raw.get("use_compression", False)),
            use_verifier=bool(raw.get("use_verifier", False)),
            use_redblue=bool(raw.get("use_redblue", False)),
            planner_mode=str(raw.get("planner_mode", "heuristic")),
        )
    return configs


class EvaluationRunner:
    def __init__(
        self,
        coordinator: ResearchCoordinator | None = None,
        judge: JudgeBackend | None = None,
        bootstrap_samples: int = 300,
    ) -> None:
        self.coordinator = coordinator or ResearchCoordinator()
        self.judge = judge or MockJudgeBackend()
        self.bootstrap_samples = bootstrap_samples

    async def run_dataset(self, dataset_path: str | Path) -> tuple[list[EvaluationResult], list[ResearchReport]]:
        cases = load_benchmark(dataset_path)
        results: list[EvaluationResult] = []
        reports: list[ResearchReport] = []
        for case in cases:
            report = await self.coordinator.run(case.question)
            reports.append(report)
            judge_score = await self.judge.score(report, case)
            results.append(self._metrics(case, report, judge_score))
        scores = [result.judge_score.overall for result in results]
        ci = bootstrap_ci(scores, samples=self.bootstrap_samples) if scores else None
        for result in results:
            result.bootstrap_ci = ci
        return results, reports

    def _metrics(self, case: BenchmarkCase, report: ResearchReport, judge_score) -> EvaluationResult:
        supported = sum(
            1
            for claim in report.claims
            if claim.verification_status in {VerificationStatus.SUPPORTED, VerificationStatus.PARTIAL}
        )
        total = max(len(report.claims), 1)
        hallucinated = sum(
            1
            for claim in report.claims
            if claim.verification_status
            in {VerificationStatus.UNSUPPORTED, VerificationStatus.CONTRADICTED}
        )
        weak = hallucinated + sum(
            1
            for claim in report.claims
            if claim.needs_verification or claim.verification_status == VerificationStatus.UNKNOWN
        )
        citation_coverage = sum(1 for claim in report.claims if claim.citation_ids) / total
        atomic_results = [
            atomic
            for claim in report.claims
            if claim.verification_trace
            for atomic in claim.verification_trace.atomic_results
        ]
        supported_atomic = sum(
            1 for atomic in atomic_results if atomic.status == VerificationStatus.SUPPORTED
        )
        contradicted_atomic = sum(
            1 for atomic in atomic_results if atomic.status == VerificationStatus.CONTRADICTED
        )
        evidence_grounding_score = (
            sum((atomic.term_overlap + atomic.quote_overlap) / 2 for atomic in atomic_results)
            / len(atomic_results)
            if atomic_results
            else citation_coverage
        )
        weak_claim_ids = {
            claim.id
            for claim in report.claims
            if claim.needs_verification
            or claim.verification_status
            in {
                VerificationStatus.UNKNOWN,
                VerificationStatus.UNSUPPORTED,
                VerificationStatus.CONTRADICTED,
                VerificationStatus.PARTIAL,
            }
        }
        repaired_targets = {
            action.target_claim_id
            for action in report.repair_actions
            if action.target_claim_id != "report.limitations"
        }
        repair_coverage = (
            len(weak_claim_ids & repaired_targets) / len(weak_claim_ids)
            if weak_claim_ids
            else (1.0 if report.repair_actions else 0.0)
        )
        repair_precision = (
            sum(
                1
                for action in report.repair_actions
                if action.target_claim_id == "report.limitations"
                or action.target_claim_id in weak_claim_ids
                or action.action_type.value == "verify"
            )
            / len(report.repair_actions)
            if report.repair_actions
            else 0.0
        )
        summary = report.run_summary
        failure_analysis = []
        for prohibited in case.must_not_claim:
            if prohibited.lower() in report.to_markdown().lower():
                failure_analysis.append(f"Report contains prohibited claim cue: {prohibited}")
        if weak:
            failure_analysis.append(f"{weak} claims require stronger support.")
        return EvaluationResult(
            question_id=case.id,
            answer_type=case.answer_type,
            factual_accuracy=supported / total,
            hallucination_rate=hallucinated / total,
            citation_coverage=citation_coverage,
            unsupported_claim_rate=weak / total,
            judge_score=judge_score,
            weak_support_rate=weak / total,
            evidence_reuse_rate=summary.get("recalled_evidence_count", 0)
            / max(summary.get("evidence_count", 1), 1),
            compression_ratio=summary.get("compression_ratio", 1.0),
            repair_success_rate=summary.get("repair_success_rate", 0.0),
            atomic_support_rate=supported_atomic / len(atomic_results) if atomic_results else 0.0,
            contradiction_detection_rate=(
                contradicted_atomic / len(atomic_results) if atomic_results else 0.0
            ),
            repair_precision=repair_precision,
            repair_coverage=repair_coverage,
            repair_convergence_rate=1.0 if summary.get("repair_converged", False) else 0.0,
            repair_oscillation_rate=(
                1.0 if summary.get("repair_oscillation_detected", False) else 0.0
            ),
            avg_repair_rounds=float(summary.get("repair_rounds_used", 0)),
            evidence_grounding_score=evidence_grounding_score,
            avg_task_latency=summary.get("avg_task_latency", 0.0),
            domain=case.domain,
            required_hops=case.required_hops,
            hotpot_style=case.hotpot_style,
            repair_action_counts=dict(
                Counter(action.action_type.value for action in report.repair_actions)
            ),
            failure_analysis=failure_analysis,
        )


def load_benchmark(path: str | Path) -> list[BenchmarkCase]:
    cases: list[BenchmarkCase] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        cases.append(
            BenchmarkCase(
                id=raw["id"],
                question=raw["question"],
                gold_points=raw.get("gold_points", []),
                tags=raw.get("tags", []),
                required_sources=raw.get("required_sources", []),
                must_not_claim=raw.get("must_not_claim", []),
                difficulty=raw.get("difficulty", "medium"),
                answer_type=raw.get("answer_type", infer_answer_type(raw.get("tags", []))),
                required_hops=raw.get("required_hops", 2 if "multihop" in raw.get("tags", []) else 1),
                domain=raw.get("domain", infer_domain(raw.get("tags", []))),
                hotpot_style=bool(raw.get("hotpot_style", "hotpot" in raw.get("tags", []))),
                expected_failure_modes=raw.get("expected_failure_modes", []),
                must_cite_sources=raw.get("must_cite_sources", []),
            )
        )
    return cases


def summarize_dataset_file(path: str | Path, default_suite_source: str) -> dict:
    answer_type_counts: Counter[str] = Counter()
    difficulty_counts: Counter[str] = Counter()
    suite_source_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    required_hops: list[int] = []
    multi_hop_count = 0
    hotpot_style_count = 0
    case_count = 0
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        tags = raw.get("tags", [])
        answer_type = raw.get("answer_type", infer_answer_type(tags))
        domain = raw.get("domain", infer_domain(tags))
        suite_source = raw.get("suite_source", default_suite_source)
        hops = raw.get("required_hops", 2 if "multihop" in tags else 1)
        answer_type_counts[answer_type] += 1
        domain_counts[domain] += 1
        difficulty_counts[raw.get("difficulty", "medium")] += 1
        suite_source_counts[suite_source] += 1
        required_hops.append(hops)
        if hops >= 2:
            multi_hop_count += 1
        if raw.get("hotpot_style", "hotpot" in tags):
            hotpot_style_count += 1
        case_count += 1
    average_required_hops = sum(required_hops) / len(required_hops) if required_hops else 0.0
    return {
        "path": str(path),
        "case_count": case_count,
        "answer_type_counts": dict(answer_type_counts),
        "domain_counts": dict(domain_counts),
        "difficulty_counts": dict(difficulty_counts),
        "suite_source_counts": dict(suite_source_counts),
        "average_required_hops": average_required_hops,
        "multi_hop_count": multi_hop_count,
        "hotpot_style_count": hotpot_style_count,
    }


def infer_answer_type(tags: list[str]) -> str:
    if "comparison" in tags:
        return "technical_comparison"
    if "multihop" in tags:
        return "multi_hop_reasoning"
    if "failure" in tags or "repair" in tags:
        return "risk_analysis"
    if "architecture" in tags or "planner" in tags:
        return "solution_design"
    return "factual_explanation"


def infer_domain(tags: list[str]) -> str:
    tag_set = set(tags)
    if tag_set & {"dag", "state-machine", "asyncio", "planner"}:
        return "agent_orchestration"
    if tag_set & {"memory", "sqlite", "embedding", "numpy"}:
        return "memory_retrieval"
    if tag_set & {"citation", "verification", "hallucination"}:
        return "citation_verification"
    if tag_set & {"redblue", "repair"}:
        return "redblue_repair"
    if tag_set & {"eval", "metrics", "judge"}:
        return "evaluation"
    if tag_set & {"llm", "llm-backend"}:
        return "llm_backend"
    if tag_set & {"compression", "textrank"}:
        return "context_compression"
    if tag_set & {"rag", "retrieval"}:
        return "rag_system"
    if tag_set & {"failure", "reliability", "offline"}:
        return "reliability"
    if tag_set & {"multihop", "hotpot"}:
        return "multi_hop"
    return "engineering_tradeoff"


def summarize_results(
    results: list[EvaluationResult],
    comparison_results: list[EvaluationResult] | None = None,
    bootstrap_samples: int = 300,
) -> dict:
    if not results:
        return {}
    overall = [result.judge_score.overall for result in results]
    comparison = (
        [result.judge_score.overall for result in comparison_results]
        if comparison_results
        else [0.5 for _ in overall]
    )
    ci = bootstrap_ci(overall, samples=bootstrap_samples)
    return {
        "n": len(results),
        "judge_score_mean": sum(overall) / len(overall),
        "judge_score_bootstrap_95_ci": list(ci),
        "cohens_d": cohens_d(comparison, overall),
        **{field: mean_result_field(results, field) for field in SUMMARY_MEAN_FIELDS},
        "per_category": summarize_by_category(results),
        "per_domain": summarize_by_domain(results),
        "judge_score_dimensions": summarize_judge_dimensions(results),
        "multi_hop_subset": summarize_subset(
            [result for result in results if result.required_hops >= 2]
        ),
        "hotpot_style_subset": summarize_subset(
            [result for result in results if result.hotpot_style]
        ),
        "repair_action_distribution": summarize_repair_actions(results),
    }


def mean_result_field(results: list[EvaluationResult], field: str) -> float:
    return sum(float(getattr(result, field)) for result in results) / len(results)


def validate_eval_payload(payload: dict, tolerance: float = 1e-9) -> None:
    for experiment_name, experiment in payload.get("experiments", {}).items():
        results = experiment.get("results", [])
        summary = experiment.get("summary", {})
        for index, result in enumerate(results):
            missing = REQUIRED_RESULT_FIELDS - set(result)
            if missing:
                raise ValueError(
                    f"{experiment_name}[{index}] missing result fields: {sorted(missing)}"
                )
            judge_score = result.get("judge_score", {})
            missing_judge = REQUIRED_JUDGE_FIELDS - set(judge_score)
            if missing_judge:
                raise ValueError(
                    f"{experiment_name}[{index}] missing judge fields: {sorted(missing_judge)}"
                )
        for field in SUMMARY_MEAN_FIELDS:
            if not results:
                continue
            expected = sum(float(result[field]) for result in results) / len(results)
            actual = float(summary.get(field, 0.0))
            if abs(expected - actual) > tolerance:
                raise ValueError(
                    f"{experiment_name} summary field {field}={actual} "
                    f"does not match result mean {expected}."
                )
        if results:
            expected_judge = (
                sum(float(result["judge_score"]["overall"]) for result in results) / len(results)
            )
            actual_judge = float(summary.get("judge_score_mean", 0.0))
            if abs(expected_judge - actual_judge) > tolerance:
                raise ValueError(
                    f"{experiment_name} summary judge_score_mean={actual_judge} "
                    f"does not match result mean {expected_judge}."
                )


def summarize_by_category(results: list[EvaluationResult]) -> dict[str, dict[str, float]]:
    buckets: dict[str, list[EvaluationResult]] = defaultdict(list)
    for result in results:
        buckets[result.answer_type].append(result)
    summary = {}
    for category, items in buckets.items():
        summary[category] = {
            "n": len(items),
            "judge_score_mean": sum(item.judge_score.overall for item in items) / len(items),
            "hallucination_rate": sum(item.hallucination_rate for item in items) / len(items),
            "weak_support_rate": sum(item.weak_support_rate for item in items) / len(items),
            "citation_coverage": sum(item.citation_coverage for item in items) / len(items),
            "atomic_support_rate": sum(item.atomic_support_rate for item in items) / len(items),
            "evidence_grounding_score": sum(item.evidence_grounding_score for item in items) / len(items),
        }
    return summary


def summarize_by_domain(results: list[EvaluationResult]) -> dict[str, dict[str, float]]:
    buckets: dict[str, list[EvaluationResult]] = defaultdict(list)
    for result in results:
        buckets[result.domain].append(result)
    return {domain: summarize_subset(items) for domain, items in buckets.items()}


def summarize_subset(results: list[EvaluationResult]) -> dict[str, float]:
    if not results:
        return {
            "n": 0,
            "judge_score_mean": 0.0,
            "hallucination_rate": 0.0,
            "weak_support_rate": 0.0,
            "citation_coverage": 0.0,
            "atomic_support_rate": 0.0,
            "repair_precision": 0.0,
            "repair_coverage": 0.0,
        }
    return {
        "n": len(results),
        "judge_score_mean": sum(item.judge_score.overall for item in results) / len(results),
        "hallucination_rate": sum(item.hallucination_rate for item in results) / len(results),
        "weak_support_rate": sum(item.weak_support_rate for item in results) / len(results),
        "citation_coverage": sum(item.citation_coverage for item in results) / len(results),
        "atomic_support_rate": sum(item.atomic_support_rate for item in results) / len(results),
        "repair_precision": sum(item.repair_precision for item in results) / len(results),
        "repair_coverage": sum(item.repair_coverage for item in results) / len(results),
    }


def summarize_repair_actions(results: list[EvaluationResult]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for result in results:
        counts.update(result.repair_action_counts)
    return dict(counts)


def summarize_judge_dimensions(results: list[EvaluationResult]) -> dict[str, float]:
    return {
        "factuality": sum(item.judge_score.factuality for item in results) / len(results),
        "coverage": sum(item.judge_score.coverage for item in results) / len(results),
        "citation_quality": sum(item.judge_score.citation_quality for item in results) / len(results),
        "structure": sum(item.judge_score.structure for item in results) / len(results),
        "usefulness": sum(item.judge_score.usefulness for item in results) / len(results),
    }


async def run_experiment(
    dataset_path: str | Path,
    config: ExperimentConfig,
    memory_path: str | Path,
    vector_path: str | Path,
    plan_dir: str | Path,
    bootstrap_samples: int = 300,
) -> tuple[list[EvaluationResult], list[ResearchReport]]:
    coordinator = ResearchCoordinator(
        memory_path=memory_path,
        vector_path=vector_path,
        plan_dir=plan_dir,
        use_memory_recall=config.use_memory_recall,
        use_compression=config.use_compression,
        use_verifier=config.use_verifier,
        use_redblue=config.use_redblue,
        planner_mode=config.planner_mode,
    )
    runner = EvaluationRunner(coordinator=coordinator, bootstrap_samples=bootstrap_samples)
    return await runner.run_dataset(dataset_path)
