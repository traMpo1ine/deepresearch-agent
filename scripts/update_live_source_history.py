from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.live_source_history import (  # noqa: E402
    append_live_source_snapshot,
    build_live_source_snapshot,
    live_source_history_markdown,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Append one live-source evaluation to history.")
    parser.add_argument("--metrics", required=True)
    parser.add_argument("--history", default="reports/live_source_history/history.jsonl")
    parser.add_argument("--report", default="reports/live_source_history/report.md")
    parser.add_argument("--run-id", default=os.getenv("GITHUB_RUN_ID"))
    parser.add_argument("--fail-on-error", action="store_true")
    args = parser.parse_args()

    metrics = json.loads(Path(args.metrics).read_text(encoding="utf-8"))
    snapshot = build_live_source_snapshot(metrics, run_id=args.run_id)
    history_path = Path(args.history)
    history = append_live_source_snapshot(history_path, snapshot)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(live_source_history_markdown(history), encoding="utf-8")
    print(f"Live-source history observations: {len(history)}")
    print(f"Latest success rate: {snapshot['success_rate']:.3f}")
    print(f"Report: {report_path}")
    if args.fail_on_error and float(snapshot["success_rate"]) < 1.0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
