from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deepresearch_agent.evaluation_cases import (  # noqa: E402
    evaluation_payload_to_markdown,
    get_evaluation_example_set,
    inspect_evaluation_case,
    list_evaluation_cases_markdown,
    load_evaluation_example_sets,
    payload_json,
)


def run(case_id: str | None, list_only: bool, as_json: bool, bootstrap_samples: int) -> None:
    if list_only:
        examples = load_evaluation_example_sets()
        if as_json:
            print(
                payload_json(
                    {
                        "cases": [
                            {
                                "id": case.case_id,
                                "baseline_rows": len(case.baseline),
                                "improved_rows": len(case.improved),
                            }
                            for case in examples.values()
                        ]
                    }
                )
            )
        else:
            print(list_evaluation_cases_markdown(examples))
        return

    case = get_evaluation_example_set(case_id or "baseline_vs_redblue")
    payload = inspect_evaluation_case(case, bootstrap_samples=bootstrap_samples)
    print(payload_json(payload) if as_json else evaluation_payload_to_markdown(payload))


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect evaluation metrics on fixed examples.")
    parser.add_argument("--case", help="Evaluation case id. Defaults to baseline_vs_redblue.")
    parser.add_argument("--list", action="store_true", help="List available evaluation examples.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    parser.add_argument("--bootstrap-samples", type=int, default=300)
    args = parser.parse_args()
    run(args.case, args.list, args.json, args.bootstrap_samples)


if __name__ == "__main__":
    main()
