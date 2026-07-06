from __future__ import annotations

import argparse
import asyncio
import json
import sys
from uuid import uuid4
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.config import config_get, load_config  # noqa: E402
from deepresearch_agent.evaluation import (  # noqa: E402
    EvalIntegrityReport,
    experiment_configs_from_config,
    run_experiment,
    summarize_dataset_file,
    summarize_results,
    validate_eval_payload,
)


def build_eval_run_id(suite: str) -> str:
    safe_suite = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in suite)
    return f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{safe_suite}_{uuid4().hex[:8]}"


async def run(
    dataset: str,
    suite: str,
    output: str | None,
    memory_path: str,
    vector_path: str,
    plan_dir: str,
    experiments: str,
    summary_markdown: str | None,
    experiment_dir: str | None,
    experiment_configs: dict,
    bootstrap_samples: int,
) -> None:
    run_id = build_eval_run_id(suite)
    base_dir = Path(experiment_dir) if experiment_dir else Path("reports") / "experiments" / run_id
    dataset_path, suite_sources = materialize_suite_dataset(suite, dataset, base_dir)
    output_path = Path(output) if output else base_dir / "metrics.json"
    summary_path = Path(summary_markdown) if summary_markdown else base_dir / "summary.md"
    failure_path = base_dir / "failure_cases.md"
    plan_root = Path(plan_dir) if plan_dir else base_dir / "plans"
    names = [name.strip() for name in experiments.split(",") if name.strip()]
    unknown = [name for name in names if name not in experiment_configs]
    if unknown:
        raise SystemExit(f"Unknown experiments: {', '.join(unknown)}")

    experiment_payloads = {}
    experiment_artifacts = {}
    baseline_results = None
    for name in names:
        config = experiment_configs[name]
        exp_memory = Path(memory_path)
        exp_vector = Path(vector_path)
        if len(names) > 1:
            exp_memory = exp_memory.with_name(f"{exp_memory.stem}_{name}{exp_memory.suffix}")
            exp_vector = exp_vector.with_name(f"{exp_vector.stem}_{name}{exp_vector.suffix}")
        results, reports = await run_experiment(
            dataset_path,
            config,
            exp_memory,
            exp_vector,
            plan_root / name,
            bootstrap_samples,
        )
        summary = summarize_results(results, baseline_results, bootstrap_samples)
        if name == "baseline":
            baseline_results = results
        experiment_payloads[name] = {
            "config": {
                "name": config.name,
                "use_memory_recall": config.use_memory_recall,
                "use_compression": config.use_compression,
                "use_verifier": config.use_verifier,
                "use_redblue": config.use_redblue,
                "planner_mode": config.planner_mode,
            },
            "summary": summary,
            "results": [result_to_dict(result) for result in results],
            "reports": [report.to_dict() for report in reports],
        }
        experiment_artifacts[name] = {
            "memory_path": str(exp_memory),
            "vector_path": str(exp_vector),
            "plan_dir": str(plan_root / name),
        }

    payload = {
        "dataset": str(dataset_path),
        "suite": suite,
        "suite_sources": suite_sources,
        "run_id": run_id,
        "bootstrap_samples": bootstrap_samples,
        "experiments": experiment_payloads,
    }
    validate_eval_payload(payload)
    dataset_summary = summarize_dataset_file(dataset_path, suite if suite != "all" else "unknown")
    payload["integrity_report"] = EvalIntegrityReport(
        config_snapshot={
            "dataset": dataset,
            "materialized_dataset": str(dataset_path),
            "suite": suite,
            "suite_sources": suite_sources,
            "experiments": names,
            "bootstrap_samples": bootstrap_samples,
            "memory_path": memory_path,
            "vector_path": vector_path,
            "plan_dir": str(plan_root),
        },
        dataset_summary=dataset_summary,
        suite_source_counts=dataset_summary["suite_source_counts"],
        payload_validation_status="passed",
        payload_validation_error=None,
        experiment_artifacts=experiment_artifacts,
    ).to_dict()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown = experiment_summary_markdown(payload)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(markdown, encoding="utf-8")
    failure_path.parent.mkdir(parents=True, exist_ok=True)
    failure_path.write_text(failure_cases_markdown(payload), encoding="utf-8")
    print(json.dumps({name: value["summary"] for name, value in experiment_payloads.items()}, ensure_ascii=False, indent=2))


def result_to_dict(result) -> dict:
    return {
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
        "judge_score": {
            "factuality": result.judge_score.factuality,
            "coverage": result.judge_score.coverage,
            "citation_quality": result.judge_score.citation_quality,
            "structure": result.judge_score.structure,
            "usefulness": result.judge_score.usefulness,
            "overall": result.judge_score.overall,
        },
        "bootstrap_ci": result.bootstrap_ci,
        "cohens_d": result.cohens_d,
    }


def experiment_summary_markdown(payload: dict) -> str:
    lines = [
        "# DeepResearch Agent Experiment Summary",
        "",
        f"Dataset: `{payload['dataset']}`",
        f"Suite: `{payload.get('suite', 'researchbench')}`",
        f"Cases: `{payload.get('integrity_report', {}).get('dataset_summary', {}).get('case_count', 0)}`",
        f"Payload validation: `{payload.get('integrity_report', {}).get('payload_validation_status', 'unknown')}`",
        "",
        "| experiment | judge | 95% CI | hallucination | weak support | citation | atomic support | repair precision | repair coverage | convergence | oscillation | rounds | Cohen's d |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, exp in payload["experiments"].items():
        summary = exp["summary"]
        ci = summary.get("judge_score_bootstrap_95_ci", [0, 0])
        lines.append(
            f"| {name} | {summary.get('judge_score_mean', 0):.3f} | "
            f"[{ci[0]:.3f}, {ci[1]:.3f}] | "
            f"{summary.get('hallucination_rate', 0):.3f} | "
            f"{summary.get('weak_support_rate', 0):.3f} | "
            f"{summary.get('citation_coverage', 0):.3f} | "
            f"{summary.get('atomic_support_rate', 0):.3f} | "
            f"{summary.get('repair_precision', 0):.3f} | "
            f"{summary.get('repair_coverage', 0):.3f} | "
            f"{summary.get('repair_convergence_rate', 0):.3f} | "
            f"{summary.get('repair_oscillation_rate', 0):.3f} | "
            f"{summary.get('avg_repair_rounds', 0):.3f} | "
            f"{summary.get('cohens_d', 0):.3f} |"
        )
    lines.extend(["", "## Judge Dimensions", ""])
    for name, exp in payload["experiments"].items():
        dims = exp["summary"].get("judge_score_dimensions", {})
        if not dims:
            continue
        lines.append(
            f"- `{name}`: factuality={dims.get('factuality', 0):.3f}, "
            f"coverage={dims.get('coverage', 0):.3f}, "
            f"citation_quality={dims.get('citation_quality', 0):.3f}, "
            f"structure={dims.get('structure', 0):.3f}, "
            f"usefulness={dims.get('usefulness', 0):.3f}"
        )
    lines.extend(["", "## Failure Cases", ""])
    for name, exp in payload["experiments"].items():
        failures = [
            (result["question_id"], result["failure_analysis"])
            for result in exp["results"]
            if result["failure_analysis"]
        ][:5]
        lines.append(f"### {name}")
        if not failures:
            lines.append("- No heuristic failure cases were detected.")
        else:
            for question_id, failure_analysis in failures:
                lines.append(f"- `{question_id}`: {'; '.join(failure_analysis)}")
        lines.append("")
    lines.extend(["", "## Per-Category Metrics", ""])
    for name, exp in payload["experiments"].items():
        lines.append(f"### {name}")
        per_category = exp["summary"].get("per_category", {})
        if not per_category:
            lines.append("- No category metrics.")
        else:
            lines.append("| category | n | judge | hallucination | weak support | citation |")
            lines.append("|---|---:|---:|---:|---:|---:|")
            for category, metrics in per_category.items():
                lines.append(
                    f"| {category} | {metrics['n']} | {metrics['judge_score_mean']:.3f} | "
                    f"{metrics['hallucination_rate']:.3f} | {metrics['weak_support_rate']:.3f} | "
                    f"{metrics['citation_coverage']:.3f} |"
                )
        lines.append("")
    lines.extend(["", "## Per-Domain Metrics", ""])
    for name, exp in payload["experiments"].items():
        lines.append(f"### {name}")
        per_domain = exp["summary"].get("per_domain", {})
        if not per_domain:
            lines.append("- No domain metrics.")
        else:
            lines.append("| domain | n | judge | hallucination | weak support | repair precision |")
            lines.append("|---|---:|---:|---:|---:|---:|")
            for domain, metrics in per_domain.items():
                lines.append(
                    f"| {domain} | {metrics['n']} | {metrics['judge_score_mean']:.3f} | "
                    f"{metrics['hallucination_rate']:.3f} | {metrics['weak_support_rate']:.3f} | "
                    f"{metrics['repair_precision']:.3f} |"
                )
        lines.append("")
    lines.extend(["", "## Multi-Hop And Hotpot Subsets", ""])
    for name, exp in payload["experiments"].items():
        multi_hop = exp["summary"].get("multi_hop_subset", {})
        hotpot = exp["summary"].get("hotpot_style_subset", {})
        lines.append(
            f"- `{name}` multi-hop: n={multi_hop.get('n', 0)}, "
            f"judge={multi_hop.get('judge_score_mean', 0):.3f}, "
            f"repair_precision={multi_hop.get('repair_precision', 0):.3f}"
        )
        lines.append(
            f"- `{name}` hotpot-style: n={hotpot.get('n', 0)}, "
            f"judge={hotpot.get('judge_score_mean', 0):.3f}, "
            f"repair_precision={hotpot.get('repair_precision', 0):.3f}"
        )
    lines.extend(["", "## Repair Action Distribution", ""])
    for name, exp in payload["experiments"].items():
        distribution = exp["summary"].get("repair_action_distribution", {})
        if distribution:
            values = ", ".join(f"{key}={value}" for key, value in sorted(distribution.items()))
        else:
            values = "none"
        lines.append(f"- `{name}`: {values}")
    integrity = payload.get("integrity_report", {})
    if integrity:
        lines.extend(["", "## Integrity Report", ""])
        suite_counts = integrity.get("suite_source_counts", {})
        artifacts = integrity.get("experiment_artifacts", {})
        lines.append(f"- Dataset summary: `{integrity.get('dataset_summary', {})}`")
        lines.append(f"- Suite source counts: `{suite_counts}`")
        lines.append(f"- Experiment artifacts: `{artifacts}`")
    return "\n".join(lines)


def failure_cases_markdown(payload: dict) -> str:
    lines = ["# Failure Cases", ""]
    for name, exp in payload["experiments"].items():
        lines.append(f"## {name}")
        failures = [
            result
            for result in exp["results"]
            if result["failure_analysis"]
        ]
        if not failures:
            lines.append("- No heuristic failure cases were detected.")
            lines.append("")
            continue
        for result in failures:
            lines.append(f"- `{result['question_id']}` ({result['answer_type']}): {'; '.join(result['failure_analysis'])}")
        lines.append("")
    return "\n".join(lines)


def resolve_eval_settings(args, config: dict) -> dict:
    return {
        "dataset": args.dataset
        or config_get(config, "evaluation.dataset", "data/benchmarks/researchbench.jsonl"),
        "suite": args.suite or config_get(config, "evaluation.suite", "researchbench"),
        "memory_path": args.memory_path
        or config_get(config, "memory.sqlite_path", "data/memory/deepresearch.sqlite3"),
        "vector_path": args.vector_path
        or config_get(config, "memory.vector_path", "data/memory/vector_index.npz"),
        "plan_dir": args.plan_dir or config_get(config, "pipeline.plan_dir", "reports/plans"),
        "experiments": args.experiments or config_get(config, "evaluation.experiments", "full"),
        "bootstrap_samples": int(config_get(config, "evaluation.bootstrap_samples", 300)),
    }


def materialize_suite_dataset(suite: str, dataset: str, base_dir: Path) -> tuple[Path, list[str]]:
    researchbench = Path(dataset)
    adversarial = Path("data/benchmarks/adversarial_researchbench.jsonl")
    if suite == "researchbench":
        return researchbench, ["researchbench"]
    if suite == "adversarial":
        return adversarial, ["adversarial"]
    if suite == "all":
        combined = base_dir / "combined_suite.jsonl"
        combined.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        for suite_source, path in (("researchbench", researchbench), ("adversarial", adversarial)):
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                item = json.loads(line)
                item["suite_source"] = suite_source
                lines.append(json.dumps(item, ensure_ascii=False))
        combined.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return combined, ["researchbench", "adversarial"]
    raise SystemExit(f"Unknown suite: {suite}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run offline DeepResearch Agent evaluation.")
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--suite", default=None, choices=["researchbench", "adversarial", "all"])
    parser.add_argument("--config", default="configs/default.toml")
    parser.add_argument("--output", default=None)
    parser.add_argument("--memory-path", default=None)
    parser.add_argument("--vector-path", default=None)
    parser.add_argument("--plan-dir", default=None)
    parser.add_argument("--experiments", default=None)
    parser.add_argument("--summary-markdown", default=None)
    parser.add_argument("--experiment-dir", default=None)
    parser.add_argument("--group-by", choices=["domain"], default=None)
    args = parser.parse_args()
    config = load_config(args.config)
    experiment_configs = experiment_configs_from_config(config)
    settings = resolve_eval_settings(args, config)
    asyncio.run(
        run(
            settings["dataset"],
            settings["suite"],
            args.output,
            settings["memory_path"],
            settings["vector_path"],
            settings["plan_dir"],
            settings["experiments"],
            args.summary_markdown,
            args.experiment_dir,
            experiment_configs,
            settings["bootstrap_samples"],
        )
    )


if __name__ == "__main__":
    main()
