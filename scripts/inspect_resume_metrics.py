from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.evaluation.runner import summarize_dataset_file  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect resume-friendly DeepResearch metrics.")
    parser.add_argument("--base", default="data/benchmarks/researchbench.jsonl")
    parser.add_argument("--extended", default="data/benchmarks/researchbench_extended.jsonl")
    parser.add_argument("--final-summary", default="reports/final/final_sprint_check/researchbench_summary.md")
    parser.add_argument("--redblue-summary", default="reports/final/final_sprint_check/redblue_fixture_eval.md")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = {
        "base_dataset": summarize_dataset_file(args.base, "researchbench"),
        "extended_dataset": summarize_dataset_file(args.extended, "researchbench_extended"),
        "latest_extended_run": _latest_extended_run(Path("reports/experiments"), args.extended),
        "resume_metric_names": [
            "repair_success_before_to_after",
            "weak_support_rate_delta",
            "atomic_support_rate_delta",
            "citation_trace_coverage",
            "redblue_fixture_repair_precision",
        ],
        "artifact_presence": {
            "researchbench_summary": Path(args.final_summary).exists(),
            "redblue_fixture_eval": Path(args.redblue_summary).exists(),
            "web_demo": Path("src/deepresearch_agent/web/app.py").exists(),
            "llm_verifier_smoke": Path("reports/llm_verifier_smoke.md").exists(),
            "corpus_profiles": Path("data/corpus/profiles/resume_agent_docs.jsonl").exists(),
        },
        "boundary": (
            "Use frozen 35-case metrics for historical baseline comparisons; the 60-case extended "
            "set now has baseline/verifier/redblue/full offline ablation, but not separate "
            "memory/compression ablations."
        ),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_to_markdown(payload))


def _to_markdown(payload: dict[str, Any]) -> str:
    extended = payload["extended_dataset"]
    latest = payload["latest_extended_run"]
    lines = [
        "# Resume Metrics Inspection",
        "",
        f"- base cases: `{payload['base_dataset']['case_count']}`",
        f"- extended cases: `{extended['case_count']}`",
        f"- extended answer types: `{extended['answer_type_counts']}`",
        f"- extended domains: `{extended['domain_counts']}`",
        f"- extended multi-hop cases: `{extended['multi_hop_count']}`",
        f"- extended hotpot-style cases: `{extended['hotpot_style_count']}`",
        f"- boundary: {payload['boundary']}",
        "",
        "## Latest Extended Benchmark",
        "",
    ]
    if latest:
        summary = latest["summary"]
        comparison = latest.get("comparison", {})
        lines.extend(
            [
                f"- run id: `{latest['run_id']}`",
                f"- profiles: `{latest.get('profiles', [])}`",
                f"- cases: `{summary['n']}`",
                f"- judge mean: `{summary['judge_score_mean']:.3f}`",
                f"- 95% CI: `{summary['judge_score_bootstrap_95_ci']}`",
                f"- hallucination_rate: `{summary['hallucination_rate']:.3f}`",
                f"- citation_coverage: `{summary['citation_coverage']:.3f}`",
                f"- repair_precision: `{summary['repair_precision']:.3f}`",
                f"- repair_coverage: `{summary['repair_coverage']:.3f}`",
            ]
        )
        if comparison:
            lines.extend(
                [
                    f"- baseline judge: `{comparison['baseline_judge']:.3f}`",
                    f"- full judge delta: `{comparison['judge_delta_full_vs_baseline']:.3f}`",
                    f"- baseline weak support: `{comparison['baseline_weak_support_rate']:.3f}`",
                    f"- full weak support: `{comparison['full_weak_support_rate']:.3f}`",
                    f"- weak support delta: `{comparison['weak_support_delta_full_vs_baseline']:.3f}`",
                ]
            )
    else:
        lines.append("- no extended benchmark run found")
    lines.extend(
        [
            "",
            "## Artifact Presence",
            "",
        ]
    )
    for key, exists in payload["artifact_presence"].items():
        lines.append(f"- {key}: `{str(exists).lower()}`")
    lines.extend(["", "## Resume Metric Names", ""])
    for name in payload["resume_metric_names"]:
        lines.append(f"- `{name}`")
    return "\n".join(lines)


def _latest_extended_run(experiment_root: Path, extended_dataset: str) -> dict[str, Any] | None:
    if not experiment_root.exists():
        return None
    candidates = sorted(
        [path for path in experiment_root.iterdir() if path.is_dir()],
        key=lambda path: path.name,
        reverse=True,
    )
    normalized_dataset = str(Path(extended_dataset))
    for directory in candidates:
        metrics_path = directory / "metrics.json"
        if not metrics_path.exists():
            continue
        try:
            payload = json.loads(metrics_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if str(Path(payload.get("dataset", ""))) != normalized_dataset:
            continue
        experiments = payload.get("experiments", {})
        full = experiments.get("full", {})
        summary = full.get("summary")
        if summary:
            baseline_summary = experiments.get("baseline", {}).get("summary", {})
            comparison = {}
            if baseline_summary:
                comparison = {
                    "baseline_judge": baseline_summary.get("judge_score_mean", 0.0),
                    "full_judge": summary.get("judge_score_mean", 0.0),
                    "judge_delta_full_vs_baseline": (
                        summary.get("judge_score_mean", 0.0)
                        - baseline_summary.get("judge_score_mean", 0.0)
                    ),
                    "baseline_weak_support_rate": baseline_summary.get("weak_support_rate", 0.0),
                    "full_weak_support_rate": summary.get("weak_support_rate", 0.0),
                    "weak_support_delta_full_vs_baseline": (
                        summary.get("weak_support_rate", 0.0)
                        - baseline_summary.get("weak_support_rate", 0.0)
                    ),
                }
            return {
                "run_id": payload.get("run_id", directory.name),
                "metrics_path": str(metrics_path),
                "summary_path": str(directory / "summary.md"),
                "profiles": sorted(experiments),
                "summary": summary,
                "comparison": comparison,
            }
    return None


if __name__ == "__main__":
    main()
