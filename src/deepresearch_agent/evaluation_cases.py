from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deepresearch_agent.evaluation.runner import summarize_results
from deepresearch_agent.schemas import EvaluationResult, JudgeScore
from deepresearch_agent.schemas.serialization import to_jsonable


DEFAULT_EVALUATION_CASES_PATH = Path("data/examples/evaluation_cases.jsonl")


@dataclass(slots=True)
class EvaluationExampleSet:
    case_id: str
    learning_notes: list[str]
    baseline: list[EvaluationResult]
    improved: list[EvaluationResult]


def load_evaluation_example_sets(
    path: str | Path = DEFAULT_EVALUATION_CASES_PATH,
) -> dict[str, EvaluationExampleSet]:
    grouped: dict[str, dict[str, Any]] = {}
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        raw = json.loads(line)
        required = {"case_id", "experiment", "question_id", "answer_type", "judge_score"}
        missing = sorted(required - set(raw))
        if missing:
            raise ValueError(f"Evaluation example line {line_number} is missing fields: {missing}")
        case_id = str(raw["case_id"])
        bucket = grouped.setdefault(case_id, {"learning_notes": [], "baseline": [], "improved": []})
        experiment = str(raw["experiment"])
        if experiment not in {"baseline", "redblue", "improved"}:
            raise ValueError(f"Unknown evaluation experiment '{experiment}' on line {line_number}")
        target = "baseline" if experiment == "baseline" else "improved"
        bucket[target].append(_result_from_raw(raw))
        if raw.get("learning_note"):
            bucket["learning_notes"].append(str(raw["learning_note"]))
    return {
        case_id: EvaluationExampleSet(
            case_id=case_id,
            learning_notes=payload["learning_notes"],
            baseline=payload["baseline"],
            improved=payload["improved"],
        )
        for case_id, payload in grouped.items()
    }


def get_evaluation_example_set(
    case_id: str,
    path: str | Path = DEFAULT_EVALUATION_CASES_PATH,
) -> EvaluationExampleSet:
    examples = load_evaluation_example_sets(path)
    if case_id not in examples:
        available = ", ".join(examples)
        raise ValueError(f"Unknown evaluation case '{case_id}'. Available cases: {available}")
    return examples[case_id]


def inspect_evaluation_case(case: EvaluationExampleSet, bootstrap_samples: int = 300) -> dict[str, Any]:
    random.seed(7)
    baseline_summary = summarize_results(case.baseline, bootstrap_samples=bootstrap_samples)
    random.seed(7)
    improved_summary = summarize_results(
        case.improved,
        comparison_results=case.baseline,
        bootstrap_samples=bootstrap_samples,
    )
    return evaluation_payload(case, baseline_summary, improved_summary)


def evaluation_payload(
    case: EvaluationExampleSet,
    baseline_summary: dict[str, Any],
    improved_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "learning_notes": case.learning_notes,
        "baseline": baseline_summary,
        "improved": improved_summary,
        "delta": {
            "judge_score_mean": improved_summary["judge_score_mean"]
            - baseline_summary["judge_score_mean"],
            "weak_support_rate": improved_summary["weak_support_rate"]
            - baseline_summary["weak_support_rate"],
            "atomic_support_rate": improved_summary["atomic_support_rate"]
            - baseline_summary["atomic_support_rate"],
            "evidence_grounding_score": improved_summary["evidence_grounding_score"]
            - baseline_summary["evidence_grounding_score"],
        },
        "interpretation": (
            "Improved config is better when judge_score_mean and atomic_support_rate increase, "
            "while weak_support_rate decreases. Cohen's d reports effect size relative to baseline."
        ),
    }


def evaluation_payload_to_markdown(payload: dict[str, Any]) -> str:
    baseline = payload["baseline"]
    improved = payload["improved"]
    delta = payload["delta"]
    lines = [
        "# Evaluation Metrics Trace",
        "",
        f"Case: `{payload['case_id']}`",
        "",
        "## Summary",
        "",
        f"Baseline judge mean: `{baseline['judge_score_mean']:.3f}`",
        f"Improved judge mean: `{improved['judge_score_mean']:.3f}`",
        f"Judge delta: `{delta['judge_score_mean']:.3f}`",
        f"Improved 95% CI: `{improved['judge_score_bootstrap_95_ci']}`",
        f"Cohen's d vs baseline: `{improved['cohens_d']:.3f}`",
        f"Weak support delta: `{delta['weak_support_rate']:.3f}`",
        f"Atomic support delta: `{delta['atomic_support_rate']:.3f}`",
        f"Evidence grounding delta: `{delta['evidence_grounding_score']:.3f}`",
        "",
        "## Interpretation",
        "",
        payload["interpretation"],
        "",
        "## Learning Notes",
        "",
    ]
    for note in payload["learning_notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines)


def list_evaluation_cases_markdown(examples: dict[str, EvaluationExampleSet]) -> str:
    lines = ["# Evaluation Cases", ""]
    for case_id, case in examples.items():
        lines.append(
            f"- `{case_id}`: {len(case.baseline)} baseline rows, {len(case.improved)} improved rows"
        )
    return "\n".join(lines)


def payload_json(payload: dict[str, Any]) -> str:
    return json.dumps(to_jsonable(payload), ensure_ascii=False, indent=2)


def _result_from_raw(raw: dict[str, Any]) -> EvaluationResult:
    score = float(raw["judge_score"])
    return EvaluationResult(
        question_id=str(raw["question_id"]),
        answer_type=str(raw["answer_type"]),
        factual_accuracy=score,
        hallucination_rate=float(raw.get("hallucination_rate", 0.0)),
        citation_coverage=float(raw.get("citation_coverage", 1.0)),
        unsupported_claim_rate=float(raw.get("weak_support_rate", 0.0)),
        judge_score=JudgeScore(score, score, score, score, score),
        weak_support_rate=float(raw.get("weak_support_rate", 0.0)),
        atomic_support_rate=float(raw.get("atomic_support_rate", 0.0)),
        repair_precision=float(raw.get("repair_precision", 0.0)),
        repair_coverage=float(raw.get("repair_coverage", 0.0)),
        evidence_grounding_score=float(raw.get("evidence_grounding_score", 0.0)),
    )
