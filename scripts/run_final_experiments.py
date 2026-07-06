from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def build_final_run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_final")


def run_command(args: list[str], log_path: Path) -> subprocess.CompletedProcess[str]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    log_path.write_text(
        "\n".join(
            [
                f"$ {sys.executable} {' '.join(args)}",
                "",
                "## STDOUT",
                result.stdout,
                "",
                "## STDERR",
                result.stderr,
                "",
                f"Exit code: {result.returncode}",
            ]
        ),
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise SystemExit(f"Command failed: {' '.join(args)}. See {log_path}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the final reproducible project evidence pack.")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument(
        "--question",
        default="为什么 DeepResearch Agent 需要引用验证？",
        help="Question used for the final showcase.",
    )
    parser.add_argument(
        "--researchbench-experiments",
        default="baseline,memory,compression,verifier,redblue,full",
    )
    parser.add_argument("--adversarial-experiments", default="baseline,verifier,redblue")
    parser.add_argument("--skip-eval", action="store_true", help="Skip full run_eval commands.")
    args = parser.parse_args()

    final_dir = Path(args.output_dir) if args.output_dir else Path("reports") / "final" / build_final_run_id()
    final_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = final_dir / "logs"
    showcase_dir = final_dir / "showcase"

    run_command(
        [
            "scripts/run_showcase.py",
            args.question,
            "--output-dir",
            str(showcase_dir),
            "--llm-backend",
            "mock",
            "--model",
            "mock-researcher-v0",
        ],
        logs_dir / "showcase.log.md",
    )

    if not args.skip_eval:
        run_command(
            [
                "scripts/run_eval.py",
                "--config",
                "configs/default.toml",
                "--experiments",
                args.researchbench_experiments,
                "--experiment-dir",
                str(final_dir / "researchbench"),
                "--summary-markdown",
                str(final_dir / "researchbench_summary.md"),
                "--output",
                str(final_dir / "researchbench_metrics.json"),
                "--memory-path",
                str(final_dir / "memory" / "researchbench.sqlite3"),
                "--vector-path",
                str(final_dir / "memory" / "researchbench_vector.npz"),
            ],
            logs_dir / "researchbench_eval.log.md",
        )
        run_command(
            [
                "scripts/run_eval.py",
                "--suite",
                "adversarial",
                "--experiments",
                args.adversarial_experiments,
                "--experiment-dir",
                str(final_dir / "adversarial"),
                "--summary-markdown",
                str(final_dir / "adversarial_summary.md"),
                "--output",
                str(final_dir / "adversarial_metrics.json"),
                "--memory-path",
                str(final_dir / "memory" / "adversarial.sqlite3"),
                "--vector-path",
                str(final_dir / "memory" / "adversarial_vector.npz"),
            ],
            logs_dir / "adversarial_eval.log.md",
        )

    run_command(
        [
            "scripts/run_redblue_eval.py",
            "--output",
            str(final_dir / "redblue_fixture_eval.md"),
        ],
        logs_dir / "redblue_fixture_eval.log.md",
    )
    run_command(
        [
            "scripts/inspect_structured_output.py",
            "--summary",
            "--output",
            str(final_dir / "structured_output_eval.md"),
        ],
        logs_dir / "structured_output_eval.log.md",
    )
    run_command(
        [
            "scripts/run_backend_smoke_matrix.py",
            "--output",
            str(final_dir / "backend_smoke_matrix.md"),
        ],
        logs_dir / "backend_smoke_matrix.log.md",
    )
    run_command(
        [
            "scripts/run_real_judge_smoke.py",
            "--backend",
            "mock",
            "--limit",
            "5",
            "--output",
            str(final_dir / "real_judge_smoke.md"),
        ],
        logs_dir / "real_judge_smoke.log.md",
    )
    run_command(
        [
            "scripts/check_project_completion.py",
            "--source-only",
            "--output",
            str(final_dir / "completion_check.md"),
        ],
        logs_dir / "completion_check.log.md",
    )

    index = {
        "final_dir": str(final_dir),
        "showcase": str(showcase_dir / "index.md"),
        "researchbench_summary": str(final_dir / "researchbench_summary.md"),
        "adversarial_summary": str(final_dir / "adversarial_summary.md"),
        "redblue_fixture_eval": str(final_dir / "redblue_fixture_eval.md"),
        "structured_output_eval": str(final_dir / "structured_output_eval.md"),
        "backend_smoke_matrix": str(final_dir / "backend_smoke_matrix.md"),
        "real_judge_smoke": str(final_dir / "real_judge_smoke.md"),
        "completion_check": str(final_dir / "completion_check.md"),
    }
    lines = [
        "# DeepResearch Agent Final Evidence Pack",
        "",
        f"Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## Artifacts",
        "",
    ]
    for name, path in index.items():
        lines.append(f"- `{name}`: `{path}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Formal project metrics are offline/mock unless a file explicitly says it is a real-provider smoke check.",
            "",
            "```json",
            json.dumps(index, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    (final_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")
    print(final_dir / "index.md")


if __name__ == "__main__":
    main()
