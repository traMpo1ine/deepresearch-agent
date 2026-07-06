from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.orchestration.stress_cases import (  # noqa: E402
    get_orchestration_stress_case,
    load_orchestration_stress_cases,
    orchestration_stress_summary,
    stress_case_to_dict,
    stress_markdown,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect orchestration stress scenarios.")
    parser.add_argument("--case", help="Stress case id.")
    parser.add_argument("--list", action="store_true", help="List cases.")
    parser.add_argument("--summary", action="store_true", help="Show stress summary.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    args = parser.parse_args()

    if args.list:
        payload = {"cases": [case.id for case in load_orchestration_stress_cases()]}
    elif args.summary or not args.case:
        payload = {"summary": orchestration_stress_summary()}
    else:
        payload = stress_case_to_dict(get_orchestration_stress_case(args.case))
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else stress_markdown(payload))


if __name__ == "__main__":
    main()
