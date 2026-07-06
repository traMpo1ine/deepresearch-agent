from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.evaluation.runner import summarize_dataset_file  # noqa: E402


DEFAULT_EXTENDED_RUN = Path("reports/experiments/20260705_020934_092414_researchbench_263e905e")
DEFAULT_FORMAL_VERIFIER = Path("reports/verifier_benchmark/formal_deepseek_v4_flash_120x3")
DEFAULT_FINAL_PACK = Path("reports/final/final_sprint_check")
DEFAULT_SCREENSHOT = Path("docs/assets/web_demo_showcase.png")


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze the pre-resume evidence pack.")
    parser.add_argument("--output-dir", default="reports/final/pre_resume_evidence_pack")
    parser.add_argument("--extended-run", default=str(DEFAULT_EXTENDED_RUN))
    parser.add_argument("--formal-verifier", default=str(DEFAULT_FORMAL_VERIFIER))
    parser.add_argument("--final-pack", default=str(DEFAULT_FINAL_PACK))
    parser.add_argument("--screenshot", default=str(DEFAULT_SCREENSHOT))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(exist_ok=True)

    extended_run = Path(args.extended_run)
    formal_verifier = Path(args.formal_verifier)
    final_pack = Path(args.final_pack)
    screenshot = Path(args.screenshot)

    _copy_if_exists(extended_run / "summary.md", output_dir / "extended_researchbench_summary.md")
    _copy_if_exists(extended_run / "metrics.json", output_dir / "extended_researchbench_metrics.json")
    _copy_if_exists(formal_verifier / "report.md", output_dir / "formal_verifier_benchmark.md")
    _copy_if_exists(formal_verifier / "aggregate.json", output_dir / "formal_verifier_benchmark.json")
    _copy_if_exists(screenshot, assets_dir / "web_demo_showcase.png")

    extended_metrics = _read_json(extended_run / "metrics.json")
    verifier_metrics = _read_json(formal_verifier / "aggregate.json")
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "output_dir": str(output_dir),
        "source_artifacts": {
            "extended_run": str(extended_run),
            "formal_verifier": str(formal_verifier),
            "final_pack": str(final_pack),
            "web_demo_screenshot": str(screenshot),
        },
        "datasets": {
            "researchbench": summarize_dataset_file("data/benchmarks/researchbench.jsonl", "researchbench"),
            "researchbench_extended": summarize_dataset_file(
                "data/benchmarks/researchbench_extended.jsonl",
                "researchbench_extended",
            ),
        },
        "extended_ablation": _extended_summary(extended_metrics),
        "formal_verifier": _formal_verifier_summary(verifier_metrics),
        "boundaries": [
            "Extended ResearchBench metrics are offline/mock pipeline metrics.",
            "Formal verifier benchmark is claim/evidence classification, not end-to-end DeepResearch quality.",
            "DeepSeek provider outputs are real API calls but remain separate from offline/mock benchmark metrics.",
            "The Web Demo is a local portfolio app, not a production multi-user SaaS.",
        ],
        "ready_for_resume_draft": True,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "index.md").write_text(_index_markdown(manifest), encoding="utf-8")
    print(output_dir / "index.md")


def _extended_summary(payload: dict[str, Any]) -> dict[str, Any]:
    experiments = payload.get("experiments", {})
    baseline = experiments.get("baseline", {}).get("summary", {})
    verifier = experiments.get("verifier", {}).get("summary", {})
    redblue = experiments.get("redblue", {}).get("summary", {})
    full = experiments.get("full", {}).get("summary", {})
    return {
        "run_id": payload.get("run_id"),
        "dataset": payload.get("dataset"),
        "profiles": sorted(experiments),
        "baseline_judge": baseline.get("judge_score_mean"),
        "verifier_judge": verifier.get("judge_score_mean"),
        "redblue_judge": redblue.get("judge_score_mean"),
        "full_judge": full.get("judge_score_mean"),
        "judge_delta_full_vs_baseline": _delta(full.get("judge_score_mean"), baseline.get("judge_score_mean")),
        "baseline_weak_support_rate": baseline.get("weak_support_rate"),
        "full_weak_support_rate": full.get("weak_support_rate"),
        "weak_support_delta_full_vs_baseline": _delta(
            full.get("weak_support_rate"),
            baseline.get("weak_support_rate"),
        ),
        "full_repair_precision": full.get("repair_precision"),
        "full_repair_coverage": full.get("repair_coverage"),
        "full_macro_note": "End-to-end pipeline metric, not verifier-only macro-F1.",
    }


def _formal_verifier_summary(payload: dict[str, Any]) -> dict[str, Any]:
    protocol = payload.get("protocol", {})
    summary = payload.get("summary", {})
    return {
        "dataset": protocol.get("dataset"),
        "model": protocol.get("model"),
        "repetitions": protocol.get("repetitions"),
        "case_count_per_repetition": protocol.get("case_count_per_repetition"),
        "total_cases": summary.get("total_cases"),
        "accuracy": summary.get("accuracy"),
        "heuristic_accuracy_mean": summary.get("heuristic_accuracy_mean"),
        "macro_precision": summary.get("macro_precision"),
        "macro_recall": summary.get("macro_recall"),
        "macro_f1": summary.get("macro_f1"),
        "estimated_cost_rmb": summary.get("estimated_cost_rmb"),
        "total_tokens": summary.get("total_tokens"),
    }


def _index_markdown(manifest: dict[str, Any]) -> str:
    extended = manifest["extended_ablation"]
    verifier = manifest["formal_verifier"]
    lines = [
        "# DeepResearch Agent Pre-Resume Evidence Pack",
        "",
        f"Generated at: `{manifest['generated_at']}`",
        "",
        "This pack freezes the evidence needed before drafting the final resume entry.",
        "",
        "## Key Artifacts",
        "",
        "- `extended_researchbench_summary.md`: 60-case extended ablation summary.",
        "- `extended_researchbench_metrics.json`: machine-readable extended ablation metrics.",
        "- `formal_verifier_benchmark.md`: 3-run DeepSeek verifier benchmark report.",
        "- `formal_verifier_benchmark.json`: machine-readable verifier benchmark aggregate.",
        "- `assets/web_demo_showcase.png`: Web Demo screenshot.",
        "",
        "## Extended ResearchBench Ablation",
        "",
        f"- run id: `{extended['run_id']}`",
        f"- profiles: `{extended['profiles']}`",
        f"- baseline judge: `{_fmt(extended['baseline_judge'])}`",
        f"- full judge: `{_fmt(extended['full_judge'])}`",
        f"- judge delta full-baseline: `{_fmt(extended['judge_delta_full_vs_baseline'])}`",
        f"- baseline weak support: `{_fmt(extended['baseline_weak_support_rate'])}`",
        f"- full weak support: `{_fmt(extended['full_weak_support_rate'])}`",
        f"- weak support delta full-baseline: `{_fmt(extended['weak_support_delta_full_vs_baseline'])}`",
        f"- full repair precision: `{_fmt(extended['full_repair_precision'])}`",
        f"- full repair coverage: `{_fmt(extended['full_repair_coverage'])}`",
        "",
        "## Formal Verifier Benchmark",
        "",
        f"- dataset: `{verifier['dataset']}`",
        f"- model: `{verifier['model']}`",
        f"- repetitions: `{verifier['repetitions']}`",
        f"- total cases: `{verifier['total_cases']}`",
        f"- DeepSeek accuracy: `{_fmt(verifier['accuracy'])}`",
        f"- heuristic accuracy mean: `{_fmt(verifier['heuristic_accuracy_mean'])}`",
        f"- macro precision: `{_fmt(verifier['macro_precision'])}`",
        f"- macro recall: `{_fmt(verifier['macro_recall'])}`",
        f"- macro F1: `{_fmt(verifier['macro_f1'])}`",
        f"- estimated cost RMB: `{verifier['estimated_cost_rmb']}`",
        "",
        "## Boundaries",
        "",
    ]
    lines.extend(f"- {item}" for item in manifest["boundaries"])
    lines.extend(
        [
            "",
            "## Manifest",
            "",
            "See `manifest.json` for structured paths, dataset summaries, and headline metrics.",
            "",
        ]
    )
    return "\n".join(lines)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _copy_if_exists(source: Path, target: Path) -> None:
    if not source.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _delta(value: Any, baseline: Any) -> float | None:
    if value is None or baseline is None:
        return None
    return float(value) - float(baseline)


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.3f}"


if __name__ == "__main__":
    main()
