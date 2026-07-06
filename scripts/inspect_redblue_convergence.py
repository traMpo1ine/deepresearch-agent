from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.redblue_convergence import (  # noqa: E402
    convergence_payload_to_markdown,
    inspect_convergence_case,
    load_convergence_cases,
    payload_json,
)


def run(case_id: str | None, list_only: bool, as_json: bool) -> None:
    if list_only:
        cases = load_convergence_cases()
        payload = {
            "cases": [
                {"id": case.case_id, "description": case.description}
                for case in cases.values()
            ]
        }
        if as_json:
            print(payload_json(payload))
        else:
            lines = ["# Red-Blue Convergence Cases", ""]
            for case in payload["cases"]:
                lines.append(f"- `{case['id']}`: {case['description']}")
            print("\n".join(lines))
        return
    payload = inspect_convergence_case(case_id or "converged")
    print(payload_json(payload) if as_json else convergence_payload_to_markdown(payload))


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect fixed Red-Blue convergence examples.")
    parser.add_argument("--case", choices=["converged", "oscillation", "max_rounds"], help="Case id. Defaults to converged.")
    parser.add_argument("--list", action="store_true", help="List available cases.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    args = parser.parse_args()
    run(args.case, args.list, args.json)


if __name__ == "__main__":
    main()
