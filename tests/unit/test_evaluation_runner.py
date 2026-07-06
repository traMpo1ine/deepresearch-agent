import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from deepresearch_agent.evaluation.judge import BenchmarkCase
from deepresearch_agent.evaluation.runner import summarize_results
from deepresearch_agent.evaluation.runner import (
    EvalIntegrityReport,
    EvaluationRunner,
    default_experiment_configs,
    experiment_configs_from_config,
    summarize_dataset_file,
    validate_eval_payload,
)
from deepresearch_agent.schemas import (
    Claim,
    EvaluationResult,
    JudgeScore,
    RepairAction,
    RepairActionType,
    ResearchReport,
    VerificationStatus,
)
RUN_EVAL_PATH = Path(__file__).resolve().parents[2] / "scripts" / "run_eval.py"
RUN_EVAL_SPEC = importlib.util.spec_from_file_location("run_eval_script", RUN_EVAL_PATH)
assert RUN_EVAL_SPEC and RUN_EVAL_SPEC.loader
run_eval_script = importlib.util.module_from_spec(RUN_EVAL_SPEC)
RUN_EVAL_SPEC.loader.exec_module(run_eval_script)
materialize_suite_dataset = run_eval_script.materialize_suite_dataset
resolve_eval_settings = run_eval_script.resolve_eval_settings
build_eval_run_id = run_eval_script.build_eval_run_id


def test_eval_run_id_uses_microseconds_and_suite_suffix() -> None:
    first = build_eval_run_id("researchbench")
    second = build_eval_run_id("researchbench")

    assert first != second
    assert "_researchbench_" in first
    assert "_researchbench_" in second
    assert len(first.split("_")) >= 5


def test_summarize_results_compares_against_real_baseline() -> None:
    baseline = [
        EvaluationResult(
            question_id="a",
            factual_accuracy=0.5,
            hallucination_rate=0.5,
            citation_coverage=0.5,
            unsupported_claim_rate=0.5,
            judge_score=JudgeScore(0.5, 0.5, 0.5, 0.5, 0.5),
        )
    ]
    improved = [
        EvaluationResult(
            question_id="a",
            factual_accuracy=1.0,
            hallucination_rate=0.0,
            citation_coverage=1.0,
            unsupported_claim_rate=0.0,
            judge_score=JudgeScore(0.8, 0.8, 0.8, 0.8, 0.8),
        )
    ]

    summary = summarize_results(improved, baseline)

    assert "cohens_d" in summary
    assert summary["weak_support_rate"] == 0.0


def test_experiment_configs_can_load_from_config_and_fallback() -> None:
    assert "baseline" in default_experiment_configs()

    configs = experiment_configs_from_config(
        {
            "experiments": {
                "profiles": [
                    {
                        "key": "tiny",
                        "name": "tiny",
                        "use_memory_recall": True,
                        "use_compression": False,
                        "use_verifier": True,
                        "use_redblue": False,
                    }
                ]
            }
        }
    )

    assert set(configs) == {"tiny"}
    assert configs["tiny"].use_memory_recall
    assert configs["tiny"].use_verifier
    assert configs["tiny"].planner_mode == "heuristic"


def test_eval_cli_settings_prefer_args_over_config() -> None:
    args = SimpleNamespace(
        dataset="cli.jsonl",
        suite="adversarial",
        memory_path="cli.sqlite3",
        vector_path=None,
        plan_dir=None,
        experiments="baseline",
    )
    config = {
        "evaluation": {
            "dataset": "config.jsonl",
            "suite": "researchbench",
            "experiments": "full",
            "bootstrap_samples": 123,
        },
        "memory": {"sqlite_path": "config.sqlite3", "vector_path": "config.npz"},
        "pipeline": {"plan_dir": "config-plans"},
    }

    settings = resolve_eval_settings(args, config)

    assert settings["dataset"] == "cli.jsonl"
    assert settings["suite"] == "adversarial"
    assert settings["memory_path"] == "cli.sqlite3"
    assert settings["vector_path"] == "config.npz"
    assert settings["plan_dir"] == "config-plans"
    assert settings["experiments"] == "baseline"
    assert settings["bootstrap_samples"] == 123


def test_validate_eval_payload_checks_required_fields_and_summary_means() -> None:
    result = EvaluationResult(
        question_id="a",
        factual_accuracy=0.8,
        hallucination_rate=0.2,
        citation_coverage=1.0,
        unsupported_claim_rate=0.2,
        judge_score=JudgeScore(0.8, 0.7, 1.0, 0.9, 0.8),
        weak_support_rate=0.2,
        atomic_support_rate=0.5,
    )
    summary = summarize_results([result])
    assert summary["judge_score_dimensions"]["factuality"] == 0.8
    assert summary["judge_score_dimensions"]["coverage"] == 0.7
    payload = {
        "experiments": {
            "baseline": {
                "summary": summary,
                "results": [
                    {
                        "question_id": result.question_id,
                        "answer_type": result.answer_type,
                        "factual_accuracy": result.factual_accuracy,
                        "hallucination_rate": result.hallucination_rate,
                        "weak_support_rate": result.weak_support_rate,
                        "citation_coverage": result.citation_coverage,
                        "unsupported_claim_rate": result.unsupported_claim_rate,
                        "evidence_reuse_rate": result.evidence_reuse_rate,
                        "compression_ratio": result.compression_ratio,
                        "repair_success_rate": result.repair_success_rate,
                        "atomic_support_rate": result.atomic_support_rate,
                        "contradiction_detection_rate": result.contradiction_detection_rate,
                        "repair_precision": result.repair_precision,
                        "repair_coverage": result.repair_coverage,
                        "repair_convergence_rate": result.repair_convergence_rate,
                        "repair_oscillation_rate": result.repair_oscillation_rate,
                        "avg_repair_rounds": result.avg_repair_rounds,
                        "evidence_grounding_score": result.evidence_grounding_score,
                        "avg_task_latency": result.avg_task_latency,
                        "domain": result.domain,
                        "required_hops": result.required_hops,
                        "hotpot_style": result.hotpot_style,
                        "repair_action_counts": result.repair_action_counts,
                        "failure_analysis": result.failure_analysis,
                        "bootstrap_ci": result.bootstrap_ci,
                        "cohens_d": result.cohens_d,
                        "judge_score": {
                            "factuality": result.judge_score.factuality,
                            "coverage": result.judge_score.coverage,
                            "citation_quality": result.judge_score.citation_quality,
                            "structure": result.judge_score.structure,
                            "usefulness": result.judge_score.usefulness,
                            "overall": result.judge_score.overall,
                        },
                    }
                ],
            }
        }
    }

    validate_eval_payload(payload)
    payload["experiments"]["baseline"]["summary"]["atomic_support_rate"] = 0.1
    with pytest.raises(ValueError, match="atomic_support_rate"):
        validate_eval_payload(payload)


def test_materialize_all_suite_records_suite_source(tmp_path: Path) -> None:
    combined, sources = materialize_suite_dataset(
        "all",
        "data/benchmarks/researchbench.jsonl",
        tmp_path,
    )

    assert sources == ["researchbench", "adversarial"]
    text = combined.read_text(encoding="utf-8")
    assert '"suite_source": "researchbench"' in text
    assert '"suite_source": "adversarial"' in text

    summary = summarize_dataset_file(combined, "unknown")
    assert summary["case_count"] == 45
    assert summary["suite_source_counts"] == {"researchbench": 35, "adversarial": 10}


def test_eval_integrity_report_serializes_expected_sections() -> None:
    report = EvalIntegrityReport(
        config_snapshot={"suite": "all", "experiments": ["baseline"]},
        dataset_summary={"case_count": 45},
        suite_source_counts={"researchbench": 35, "adversarial": 10},
        payload_validation_status="passed",
        payload_validation_error=None,
        experiment_artifacts={
            "baseline": {
                "memory_path": "baseline.sqlite3",
                "vector_path": "baseline.npz",
                "plan_dir": "plans/baseline",
            }
        },
    )

    payload = report.to_dict()

    assert payload["payload_validation_status"] == "passed"
    assert payload["dataset_summary"]["case_count"] == 45
    assert payload["experiment_artifacts"]["baseline"]["memory_path"] == "baseline.sqlite3"


def test_repair_metrics_cover_empty_valid_and_omission_repairs() -> None:
    case = BenchmarkCase("case", "q", [], [], [], [], "easy")
    judge = JudgeScore(1.0, 1.0, 1.0, 1.0, 1.0)

    supported = Claim(
        id="supported",
        text="Supported claim.",
        citation_ids=["ev"],
        verification_status=VerificationStatus.SUPPORTED,
    )
    supported_report = ResearchReport("q", "t", "s", [supported], [])
    supported_metrics = EvaluationRunner()._metrics(case, supported_report, judge)
    assert supported_metrics.repair_precision == 0.0
    assert supported_metrics.repair_coverage == 0.0

    weak = Claim(
        id="weak",
        text="Weak claim.",
        citation_ids=["ev"],
        verification_status=VerificationStatus.PARTIAL,
        needs_verification=True,
    )
    weak_report = ResearchReport("q", "t", "s", [weak], [])
    weak_report.repair_actions.append(
        RepairAction(RepairActionType.MODIFY, "weak", "partial", "qualified")
    )
    weak_metrics = EvaluationRunner()._metrics(case, weak_report, judge)
    assert weak_metrics.repair_precision == 1.0
    assert weak_metrics.repair_coverage == 1.0

    omission_report = ResearchReport("q", "t", "s", [supported], [])
    omission_report.repair_actions.append(
        RepairAction(RepairActionType.ADD, "report.limitations", "omission", "added limitation")
    )
    omission_metrics = EvaluationRunner()._metrics(case, omission_report, judge)
    assert omission_metrics.repair_precision == 1.0
    assert omission_metrics.repair_coverage == 1.0
