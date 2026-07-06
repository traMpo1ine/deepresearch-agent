from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.agents.planner import PlannerAgent  # noqa: E402
from deepresearch_agent.orchestration.inspection import (  # noqa: E402
    plan_overview,
    plan_to_markdown,
)
from deepresearch_agent.schemas.serialization import to_jsonable  # noqa: E402


async def run(
    question: str,
    output: str | None = None,
    as_json: bool = False,
    planner_mode: str = "heuristic",
) -> None:
    plan = await PlannerAgent(mode=planner_mode).plan(question)
    if as_json:
        text = json.dumps(to_jsonable(plan_overview(plan)), ensure_ascii=False, indent=2)
    else:
        text = plan_to_markdown(plan)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Planner DAG without running research.")
    parser.add_argument("question", help="Research question to plan.")
    parser.add_argument("--output", help="Optional output path.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    parser.add_argument("--planner-mode", choices=["template", "heuristic"], default="heuristic")
    args = parser.parse_args()
    asyncio.run(run(args.question, args.output, args.json, args.planner_mode))


if __name__ == "__main__":
    main()
